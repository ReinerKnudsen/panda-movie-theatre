# Lerntagebuch — Kino-App

---

## 24.03.2026 — Pydantic Grundlagen und Modelldesign

### Was war die Aufgabe?

Aufbau eines sauberen Pydantic-Datenmodells für einen Film (`MovieCreate`, `MovieResponse`) und einen Regisseur (`DirectorCreate`) — ohne Datenbank, nur mit Pydantic.

---

### Konzept 1 — Typ-Annotationen vs. Zuweisung

```python
duration_min = int   # ❌ weist das Klassenobjekt "int" zu — kein Feld
duration_min: int    # ✅ Typ-Annotation — Pydantic erkennt es als Feld
```

Ein stiller Bug: Pydantic ignoriert `= int` komplett, das Feld existiert im Objekt nicht wie erwartet.

---

### Konzept 2 — Optionale Felder brauchen einen Default

```python
description: str | None        # Pflichtfeld, darf aber None sein
description: str | None = None # Optional — kann weggelassen werden
```

`str | None` beschreibt nur den erlaubten Typ, nicht ob das Feld required ist.

---

### Konzept 3 — Enums mit str-Mix

```python
class Genre(str, Enum):
    THRILLER = "thriller"
```

`str, Enum` sorgt dafür dass JSON-Serialisierung den String-Wert `"thriller"` ausgibt, nicht den Python-Namen `"THRILLER"`.

---

### Konzept 4 — field_validator

```python
@field_validator("title")
@classmethod
def validate_title(cls, value):
    value = value.strip()
    if not value:
        raise ValueError("The title cannot be empty.")
    return value  # ← immer zurückgeben!
```

- `@classmethod` ist immer nötig
- Der Rückgabewert landet im Konstruktor (`__init__`) — man kann Werte prüfen **und** transformieren
- `return value` vergessen → Feld wird `None`

---

### Konzept 5 — Nested Models

Pydantic-Models können ineinander verschachtelt werden:

```python
class MovieCreate(BaseModel):
    director: DirectorCreate
```

Beim Erstellen akzeptiert Pydantic sowohl ein `DirectorCreate`-Objekt als auch ein einfaches Dict — Pydantic konvertiert automatisch.

---

### Konzept 6 — model_dump() und Serialisierung

```python
movie.model_dump()              # Python Dict — Enums bleiben Enum-Objekte
movie.model_dump(mode='json')   # Python Dict — alles JSON-kompatibel
movie.model_dump_json(indent=2) # echter JSON-String, gut zum Debuggen
```

Nested Models werden automatisch mitsersialisiert — Pydantic geht rekursiv durch alle Felder.
FastAPI macht `model_dump(mode='json')` intern automatisch beim Zurückgeben einer Response.

---

### Konzept 7 — computed_field

```python
@computed_field
@property
def full_name(self) -> str:
    return f"{self.first_name} {self.last_name}"
```

- `@property` macht aus einer Methode ein Attribut (kein `()` beim Aufrufen)
- `@computed_field` sorgt dafür dass das Property in `model_dump()` und JSON auftaucht
- Der Client schickt es nie mit — es wird immer serverseitig berechnet

---

### Offen / nächste Aufgabe

- ~~**Aufgabe 5**: `model_validator(mode='after')`~~ ✅ erledigt, siehe unten

---

## 27.03.2026 — model_validator, FastAPI Endpoints und CRUD

### Was war die Aufgabe?

`model_validator` kennenlernen, dann die ersten vollständigen CRUD-Endpoints für die Kino-App bauen — noch ohne Datenbank, mit In-Memory-Liste.

---

### Konzept 8 — model_validator

```python
@model_validator(mode='after')
def validate_release_year(self):
    if self.release_year and self.release_year > date.today().year:
        raise ValueError('The release year cannot be in the future.')
    return self  # ← immer self zurückgeben!
```

- Hat Zugriff auf das **fertige Objekt** (`self`) — alle Felder sind schon gesetzt
- Gibt immer `self` zurück, kein einzelner Wert
- Nötig wenn eine Regel **mehrere Felder gleichzeitig** betrifft

**Wann welchen Validator?**

|                    | `field_validator`                | `model_validator`              |
| ------------------ | -------------------------------- | ------------------------------ |
| Bekommt            | einen einzelnen Wert             | das ganze Objekt (`self`)      |
| Gibt zurück        | den (evtl. transformierten) Wert | `self`                         |
| Ist `@classmethod` | ✅ ja                            | ❌ nein                        |
| Wann               | ein Feld prüfen/transformieren   | mehrere Felder zusammen prüfen |

**Wichtige Erkenntnis:** `field_validator` ist eine Klassenmethode weil das Objekt zu dem Zeitpunkt noch nicht existiert — Pydantic prüft die Felder **vor** dem Konstruktor. `model_validator(mode='after')` läuft danach, deshalb ist dort `self` verfügbar.

---

### Konzept 9 — Short-circuit evaluation

```python
if self.release_year and self.release_year > date.today().year:
```

Python wertet `and` von links nach rechts aus. Wenn der erste Ausdruck `False` (oder `None`) ist, wird der zweite **gar nicht ausgewertet**. Das verhindert Fehler und ist gleichzeitig kompakter als zwei verschachtelte `if`s.

---

### Konzept 10 — FastAPI Endpoints und HTTP Status Codes

```python
@app.post("/movies", status_code=201)   # Created
@app.get("/movies", status_code=200)    # OK
@app.delete("/movies/{id}", status_code=200)  # OK + gelöschtes Objekt zurück
@app.put("/movies/{id}", status_code=200)     # OK + aktualisiertes Objekt
```

- `status_code` gehört in den **Decorator**, nicht in die Funktionssignatur
- `404 Not Found` — das gesuchte Objekt existiert nicht
- `422 Unprocessable Entity` — Pydantic-Validierung schlägt fehl (automatisch)
- Pydantic validiert eingehende Requests **bevor** die Funktion aufgerufen wird — kein manuelles Prüfen auf leere Felder nötig

---

### Konzept 11 — model_dump() + \*\* zum Objekt bauen

```python
movie_data = movie.model_dump()   # MovieCreate → Dict
movie_data["id"] = len(movies) + 1  # id hinzufügen
new_movie = Movie(**movie_data)   # Dict → Movie
```

`**movie_data` entpackt das Dict in Keyword-Argumente — wie Spread in JavaScript. Nötig weil `MovieCreate` keine `id` hat, `Movie` aber schon.

---

### Konzept 12 — next() für Listen

```python
movie = next((m for m in movies if m.id == id), None)
```

Gibt den ersten Treffer zurück, oder `None` wenn keiner gefunden wird. Entspricht `.first()` in SQLAlchemy — dasselbe Denkmuster, andere Syntax.

---

### Konzept 13 — setattr für dynamische Attribute

```python
for key, value in movie.model_dump().items():
    setattr(movie_to_update, key, value)
```

`setattr(obj, "title", "Inception")` ist dasselbe wie `obj.title = "Inception"` — aber mit dynamischem Attributnamen. Perfekt für Updates wo man nicht jedes Feld einzeln anfassen will. Wenn später ein neues Feld dazukommt, muss der Endpoint nicht angefasst werden.

---

### Konzept 14 — Separation of Concerns

`find_movie()` findet — der Endpoint entscheidet was bei `None` passiert. Eine Hilfsfunktion sollte keine `HTTPException` werfen, das ist Aufgabe der Route. Selbst erkannt. ✅

---

### Nächste Aufgabe

- ~~**pytest**~~ ✅ erledigt, siehe unten
- ~~**Router-Struktur**~~ ✅ erledigt, siehe unten

---

## 27.03.2026 — pytest, TestClient und Router

### Was war die Aufgabe?

Die CRUD-Endpoints mit pytest testen, Test Isolation lösen und die App mit APIRouter strukturieren.

---

### Konzept 15 — pytest und TestClient

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_get_movies():
    response = client.get("/movies")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

- Testfunktionen müssen mit `test_` beginnen — pytest findet sie automatisch
- `TestClient` simuliert HTTP-Requests ohne laufenden Server
- `assert` — wenn die Bedingung `False` ist, schlägt der Test fehl
- Tests starten mit `pytest test_movies.py -v`

---

### Konzept 16 — model_validate() — das Gegenteil von model_dump()

```python
movie.model_dump()              # Objekt → Dict
Movie.model_validate(data)      # Dict → Objekt
```

Eselsbrücke für den Alltag:

| Situation               | Lösung                                            |
| ----------------------- | ------------------------------------------------- |
| Objekt → API schicken   | `model_dump(mode='json')`                         |
| API-Antwort vergleichen | `response.json()["feld"] == "string"`             |
| Dict → Objekt bauen     | `Movie(**data)` oder `Movie.model_validate(data)` |
| Objekt updaten          | altes entfernen, neues mit `Movie(**data)` bauen  |

**Wichtig bei Nested Models:** `model_dump()` gibt den Director als Dict zurück, nicht als `DirectorCreate`-Objekt. Deshalb bei Updates immer ein neues Objekt bauen statt `setattr` zu verwenden.

---

### Konzept 17 — pytest fixture und Test Isolation

```python
@pytest.fixture(autouse=True)
def reset_movies():
    movies.clear()  # vor jedem Test
    yield
    movies.clear()  # nach jedem Test
```

- Ohne Reset: globale Liste wächst zwischen Tests — Tests beeinflussen sich gegenseitig
- `autouse=True` — fixture wird automatisch für jeden Test ausgeführt
- `yield` trennt Setup (vorher) von Teardown (nachher)
- Tests die `None` zurückgeben könnten, immer mit `assert x is not None` absichern — sonst besteht ein Test auch wenn er eigentlich fehlschlägt

---

### Konzept 18 — APIRouter

```python
# routers/movies.py
router = APIRouter(prefix="/movies", tags=["movies"])

@router.get("/{id}")   # → GET /movies/{id}
@router.post("")       # → POST /movies
```

```python
# main.py
app.include_router(movies.router)
```

- Ein Router pro Domäne — Filme, Säle, Vorstellungen, Personal
- `prefix` erspart das wiederholte `/movies` in jeder Route
- `tags` gruppiert Endpoints in der Swagger-Dokumentation
- `main.py` bleibt immer schlank — nur `include_router` Aufrufe

---

### Nächste Entscheidung

- **Datenbank anbinden** mit SQLModel
- **Typer** — CLI-Tools für die Kino-App

---

## 27.03.2026 — PostgreSQL anbinden, SQLModel und CRUD mit echter Datenbank

### Was war die Aufgabe?

Die In-Memory-Liste durch eine echte PostgreSQL-Datenbank ersetzen. Models umbauen, Tabellen erstellen, alle Endpoints anpassen.

---

### Konzept 19 — Datenbankverbindung mit SQLModel

```python
# database.py
from sqlmodel import create_engine, Session, SQLModel
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set — check your .env file")

engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
```

**Warum so?**

- `load_dotenv()` liest die `.env` Datei — Zugangsdaten niemals hardcoden oder in Git committen
- `echo=True` gibt jedes SQL-Statement in der Konsole aus — unverzichtbar zum Lernen
- `get_session()` öffnet eine Session pro Request und schließt sie automatisch nach dem `yield`
- **Fail fast**: wenn `DATABASE_URL` fehlt, sofort mit klarer Fehlermeldung abbrechen

**Connection String:**

```
postgresql://user:passwort@host:5432/datenbankname
```

---

### Konzept 20 — SQLModel: Pydantic + Datenbank in einer Klasse

```python
class DirectorCreate(SQLModel):
    first_name: str
    last_name: str
    birth_year: int | None = None

class Director(DirectorCreate, table=True):
    id: int | None = Field(default=None, primary_key=True)
```

**Warum zwei Klassen?**

- `DirectorCreate` — was der Client schickt (keine `id`, keine DB-Logik)
- `Director` — was in der Datenbank landet (mit `id`, Foreign Keys, Relationships)
- `table=True` ist der Schalter: SQLModel erstellt eine echte Tabelle

SQLModel generiert daraus automatisch:

```sql
CREATE TABLE director (
    id SERIAL NOT NULL,
    first_name VARCHAR NOT NULL,
    last_name VARCHAR NOT NULL,
    birth_year INTEGER,
    PRIMARY KEY (id)
)
```

---

### Konzept 21 — Foreign Keys und Relationships

```python
class Movie(MovieCreate, table=True):
    id: int | None = Field(default=None, primary_key=True)
    director_id: int = Field(foreign_key="director.id")       # DB-Ebene
    director: Director | None = Relationship(back_populates="movies")  # Python-Ebene
```

**Zwei verschiedene Dinge:**

- `director_id` — die echte Datenbankspalte, verweist auf `director.id`
- `director` — bequemer Python-Zugriff, kein eigenes DB-Feld

**`back_populates` schließt den Kreis:**

```python
movie.director    # → gibt den Director zurück
director.movies   # → gibt alle Filme des Directors zurück
```

**Circular Import vermeiden:**

```python
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from models.movie import Movie
# Läuft zur Laufzeit nie — aber die IDE ist glücklich
```

---

### Konzept 22 — Tabellen beim App-Start erstellen mit lifespan

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)  # ← lifespan muss übergeben werden!
```

**Wichtig:** Models müssen importiert sein bevor `create_all` läuft — sonst erstellt SQLModel keine Tabellen.

---

### Konzept 23 — CRUD Pattern mit Datenbank-Session

Jeder Endpoint bekommt eine Session per Dependency Injection:

```python
async def create_director(director: DirectorCreate, session: Session = Depends(get_session)):
```

#### Datensatz anlegen

**Pattern:**

1. Input → Datenbank-Objekt: `new_obj = Director.model_validate(director)`
2. Vormerken: `session.add(new_obj)`
3. Speichern: `session.commit()`
4. Datenbank-Werte zurücklesen: `session.refresh(new_obj)`
5. Objekt zurückgeben

#### Datensatz lesen

```python
# Alle:
directors = session.exec(select(Director)).all()

# Einzelner per ID:
director = session.get(Director, id)
if director is None:
    raise HTTPException(status_code=404, ...)
```

#### Datensatz löschen

**Pattern:**

1. Prüfe ob Datensatz existiert: `session.get(Director, id)`
2. Falls nein: `raise HTTPException(status_code=404, ...)`
3. Löschen: `session.delete(director_to_delete)`
4. Speichern: `session.commit()`
5. Gelöschtes Objekt zurückgeben (kein `refresh` nötig)

**Achtung Foreign Key:** PostgreSQL verhindert das Löschen wenn noch abhängige Datensätze existieren. Sauber abfangen mit:

```python
from sqlalchemy.exc import IntegrityError
try:
    session.delete(...)
    session.commit()
except IntegrityError:
    raise HTTPException(status_code=409, detail="Cannot delete — dependent records exist")
```

`409 Conflict` — der korrekte Status Code für diesen Fall.

---

### Konzept 24 — PATCH vs PUT

|         | `PUT`                         | `PATCH`              |
| ------- | ----------------------------- | -------------------- |
| Schickt | alle Felder                   | nur geänderte Felder |
| Schema  | Pflichtfelder bleiben Pflicht | alle Felder optional |

#### Datensatz patchen

**Voraussetzung:** Patch-Schema wo alle Felder optional sind:

```python
class DirectorPatch(SQLModel):
    first_name: str | None = None
    last_name: str | None = None
    birth_year: int | None = None
```

**Pattern:**

1. Prüfe ob Datensatz existiert: `session.get(Director, id)`
2. Falls nein: `raise HTTPException(status_code=404, ...)`
3. Nur gesetzte Felder auslesen: `patch_data = patch.model_dump(exclude_unset=True)`
4. Bestehenden Datensatz aktualisieren: `existing.sqlmodel_update(patch_data)`
5. Session ausführen: `session.add()`, `session.commit()`, `session.refresh()`
6. Aktualisiertes Objekt zurückgeben

**`exclude_unset=True`** — nur Felder die der Client wirklich geschickt hat werden übertragen.

---

### Nächste Themen

- **IntegrityError** sauber abfangen beim Löschen
- **Typer** — CLI-Tools für die Kino-App
- **Tests** anpassen für die Datenbankanbindung
