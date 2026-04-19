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

---

## 28.03.2026 — Tests mit Datenbank, IntegrityError und Typer CLI

### Was war die Aufgabe?

Tests auf echte Datenbankanbindung umstellen, IntegrityError beim Löschen sauber abfangen, und ein CLI-Tool mit Typer bauen.

---

### Konzept 25 — Tests mit SQLite in-memory und Dependency Override

```python
# conftest.py
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://",  # in-memory — kein File, nach Test weg
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def override_get_session():
        yield session
    app.dependency_overrides[get_session] = override_get_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
```

**Warum SQLite in-memory für Tests?**

- Keine echte Datenbank nötig — läuft komplett im RAM
- Nach jedem Test automatisch weg — perfekte Isolation
- Schneller als PostgreSQL übers Netzwerk

**`dependency_overrides`** — FastAPI erlaubt es, Dependencies für Tests zu ersetzen. `get_session` wird durch die Test-Session ersetzt — die App merkt nichts davon.

**Fixture als Parameter anfordern:**

```python
def test_create_director(client: TestClient):  # ← Fixture wird hier angefordert
```

Nicht `autouse=True` — nur Tests die `client` brauchen bekommen die Fixture.

---

### Konzept 26 — Arrange, Act, Assert

```python
def test_delete_director(client: TestClient):
    assert create_director(client)      # Arrange — Vorbedingung prüfen
    response = client.delete("/directors/1")  # Act — Aktion ausführen
    assert response.status_code == 200  # Assert — Ergebnis prüfen
```

`assert` ist nicht nur für die finale Prüfung — auch Vorbedingungen absichern. Ein Test der bei fehlendem Setup trotzdem grün ist, ist wertlos.

**Hilfsfunktionen in Tests:**

```python
def create_director(client: TestClient) -> bool:
    response = client.post("/directors", json=new_director.model_dump(mode="json"))
    return response.status_code == 201
```

Auslagern was mehrere Tests brauchen — aber immer mit `assert` absichern.

---

### Konzept 27 — exclude_unset=True auf beiden Seiten

PATCH-Problem: `model_dump(mode='json')` gibt alle Felder zurück — auch die `None`-Felder:

```python
DirectorPatch(birth_year=2020).model_dump(mode='json')
# → {"first_name": None, "last_name": None, "birth_year": 2020}
```

Damit ist `exclude_unset=True` im Endpoint wirkungslos — der Client hat alle Felder geschickt.

**Lösung:** `exclude_unset=True` auch beim Schicken:

```python
# In Tests:
json=patch.model_dump(mode='json', exclude_unset=True)
# → {"birth_year": 2020}

# Oder direkt als Dict:
json={"birth_year": 2020}
```

`exclude_unset=True` muss auf **beiden Seiten** angewendet werden — beim Schicken und beim Empfangen.

---

### Konzept 28 — Nur table=True Objekte können der Session hinzugefügt werden

```python
session.add(DirectorCreate(...))  # ❌ kein table=True — SQLAlchemy wirft Fehler
session.add(Director(...))        # ✅ table=True — kann gespeichert werden
```

`DirectorCreate` ist nur ein Pydantic-Schema — SQLAlchemy kennt keine Tabelle dafür.

---

### Konzept 29 — IntegrityError sauber abfangen

```python
from sqlalchemy.exc import IntegrityError

try:
    session.delete(director_to_delete)
    session.commit()
    return director_to_delete
except IntegrityError:
    raise HTTPException(
        status_code=409,
        detail=f"Director {director_to_delete.last_name} is still connected to Movies"
    )
```

- `409 Conflict` — der korrekte Status Code wenn eine Aktion einen Konflikt mit dem aktuellen Zustand verursacht
- Nacktes `except:` niemals verwenden — fängt alles ab, auch `KeyboardInterrupt` und `MemoryError`
- Exception-Typ kommt aus der Bibliothek die den Fehler wirft — Stacktrace zeigt immer den genauen Typ

---

### Konzept 30 — Typer CLI

```python
import typer

app = typer.Typer()

@app.command()
def create_director(first_name: str, last_name: str, birth_year: int | None = None):
    typer.echo(f"Director {first_name} {last_name} created")

if __name__ == "__main__":
    app()
```

**Typer liest Typ-Annotationen — genau wie FastAPI:**

- Pflichtparameter → Positionsargumente: `python3 cli.py create-director "Werner" "Herzog"`
- Optionale Parameter → `--flag`: `python3 cli.py create-director "Werner" "Herzog" --birth-year 1942`
- `typer.echo()` statt `print()` — idiomatisch, funktioniert konsistent auf allen Plattformen
- `typer.confirm()` für Bestätigungsabfragen statt `input()`

**CLI spricht direkt mit der Datenbank** — nicht über die API:

```
routers/  → HTTP-Welt
cli.py    → Terminal-Welt
models/, database.py → geteilt von beiden
```

---

### Konzept 31 — JSON laden und Seed-Datenbank

```python
import json

with open("db_seed_data.json") as f:
    data = json.load(f)  # → Python Dict
```

**Lookup-Tabelle statt verschachtelter Schleife:**

```python
# ❌ N×M Problem — für jeden Film alle Directors durchsuchen
for m in movies:
    for d in directors:
        if m["director"] == d.last_name:
            m["director_id"] = d.id

# ✅ Dict als Lookup — einmal bauen, dann O(1) Zugriff
directors_map = {d.last_name: d.id for d in directors}
for m in movies:
    m["director_id"] = directors_map[m["director"]]
```

**Dict Comprehension:** `{key: value for element in liste}` — dasselbe wie eine for-Schleife die ein Dict befüllt, in einer Zeile.

**Seed-Reihenfolge wegen Foreign Keys:**

1. Movies löschen
2. Directors löschen
3. Directors anlegen + committen
4. IDs der neuen Directors laden
5. Movies mit korrekten `director_id`s anlegen

---

### Nächste Themen

- **Rich** — schönere CLI-Ausgaben mit Tabellen und Farben
- **Auth mit FastAPI** — OAuth2, JWT Tokens, Rollen (Admin, Kassierer...)
- **Weitere Models** — Säle, Vorstellungen, Tickets
- **pyproject.toml** — CLI als installierbare Anwendung (`pmt list-movies`)

---

## 31.03.2026 — Weitere Models: Screen und Screening

### Was war die Aufgabe?

Neue Domain-Models für Kinosäle (`Screen`) und Vorstellungen (`Screening`) bauen — mit Enums, Validators, Foreign Keys und Relationships.

---

### Konzept 32 — int Enum für begrenzte Zahlenwerte

```python
class Floor(int, Enum):
    GROUND = 0
    FIRST = 1
    SECOND = 2
    THIRD = 3
```

`int, Enum` statt `str, Enum` — wenn die Werte Zahlen sind. Faustregel:

- Enum → wenn die Werte eine fachliche Bedeutung haben (`GROUND`, `FIRST`...)
- Validator → wenn es nur eine Zahlenbegrenzung ohne besondere Bedeutung ist

---

### Konzept 33 — Relationship und back_populates erklärt

`Relationship` ist kein Datenbankfeld — es ist ein Python-Shortcut:

```python
# In Movie:
director_id: int = Field(foreign_key="director.id")  # echte DB-Spalte
director: Director = Relationship(back_populates="movies")  # Python-Shortcut
```

**Ohne Relationship:**

```python
movie.director_id  # → 1
# Für den Director: extra Query nötig
```

**Mit Relationship:**

```python
movie.director  # → Director(first_name="Christopher", ...) — automatisch
```

**`back_populates` schließt den Kreis:**

```python
# In Movie:
director: Director = Relationship(back_populates="movies")

# In Director:
movies: list["Movie"] = Relationship(back_populates="director")
```

`back_populates="movies"` sagt: _"das Gegenstück auf der anderen Seite heißt `movies`"_. Der String ist der **Feldname** auf der anderen Klasse — nicht der Klassenname.

Ergebnis:

```python
movie.director      # → gibt den Director zurück
director.movies     # → gibt alle Filme des Directors zurück
```

**Relationship ist optional** — wenn du nur `screening.movie` brauchst aber nicht `movie.screenings`:

```python
# In Screening:
movie: Movie | None = Relationship()  # kein back_populates nötig
# In Movie: gar nichts
```

Der Foreign Key in der Datenbank existiert trotzdem — PostgreSQL erzwingt die Integrität. Du kannst immer noch per Query alle Screenings für einen Film holen:

```python
statement = select(Screening).where(Screening.movie_id == movie_id)
```

---

### Konzept 34 — Businesslogik gehört in den Endpoint

Das Model prüft Feldwerte — der Endpoint prüft Businessregeln die mehrere Objekte betreffen:

```python
# Model: Ist die Uhrzeit in der Vergangenheit?
@field_validator("screen_time")
def validate_screen_time(cls, value):
    if value < datetime.now():
        raise ValueError("The screening date can't be in the past")
    return value

# Endpoint: Sind noch Plätze frei? (braucht Screen UND Screening)
if screening.bookings + requested_seats > screen.capacity:
    raise HTTPException(status_code=400, detail="Not enough seats available")
```

---

### Konzept 35 — DRY: Don't Repeat Yourself

Statt in jedem Endpoint dieselbe Fehlermeldung zu schreiben:

```python
def create_error_message(id: int) -> str:
    return f"Screen with id {id} is unknown"

raise HTTPException(status_code=404, detail=create_error_message(id))
```

Wenn sich der Text ändert, nur eine Stelle anpassen. Gilt auch für `find_movie()` und andere Hilfsfunktionen.

---

### Nächste Themen

- **Screening Router** — mit Buchungslogik (Kapazitätsprüfung)
- **Auth mit FastAPI** — OAuth2, JWT Tokens, Rollen
- **Rich** — schönere CLI-Ausgaben
- **Booking Model** — Kundenbuchungen mit Platzzuweisung

---

## 10.04.2026 — Tests für Screen und Screening, flush() und Testdaten-Vorbereitung

### Was war die Aufgabe?

Tests für `Screen` und `Screening` schreiben — inklusive Business Rule Test für den DELETE Endpoint.

---

### Konzept 36 — session.flush() vs session.commit()

```python
session.add(director)
session.flush()   # schreibt in die DB — aber Transaktion bleibt offen
assert director.id is not None  # id ist jetzt verfügbar!

movie = Movie(director_id=director.id, ...)  # id kann verwendet werden
session.add(movie)
session.commit()  # Transaktion abschließen
```

|                     | `flush()`         | `commit()`              |
| ------------------- | ----------------- | ----------------------- |
| Schreibt in DB      | ✅                | ✅                      |
| Transaktion offen   | ✅ — bleibt offen | ❌ — wird abgeschlossen |
| ID verfügbar danach | ✅                | ✅                      |
| Rollback möglich    | ✅ noch           | ❌ nein                 |

`flush()` ist nützlich wenn man innerhalb einer Transaktion die vergebene ID braucht — z.B. um einen Foreign Key zu setzen.

---

### Konzept 37 — Testdaten-Vorbereitung mit Abhängigkeiten

Wenn ein Model Foreign Keys hat, müssen alle abhängigen Objekte zuerst in der DB sein. In Tests direkt über die Session — nicht über API-Endpoints:

```python
def create_screening(client: TestClient, session: Session, this_bookings: int = 0):
    # 1. Director anlegen
    director = Director(first_name="Francis", last_name="Forgiveme")
    session.add(director)
    session.flush()
    assert director.id is not None

    # 2. Movie und Screen anlegen
    movie = Movie(title="Test", director_id=director.id, ...)
    screen = Screen(number=1, capacity=200, ...)
    session.add(movie)
    session.add(screen)
    session.flush()
    session.commit()

    # 3. Screening über API anlegen
    response = client.post("/screenings", json={...})
    return Screening.model_validate(response.json())
```

**Warum direkt über Session statt API?**

- Keine Abhängigkeiten zwischen Testdateien
- Schneller — kein HTTP-Overhead
- Sauberer — jeder Test kontrolliert exakt seine Vorbedingungen

---

### Konzept 38 — Business Rule Tests

Hilfsfunktionen mit Parametern machen Tests flexibel:

```python
def create_screening(client, session, this_bookings: int = 0):
    # ...
    new_screening = ScreeningCreate(..., bookings=this_bookings)
```

Dann:

```python
def test_delete_screening_with_bookings_fails(client, session):
    new_screening = create_screening(client, session, this_bookings=30)
    response = client.delete(f"/screenings/{new_screening.id}")
    assert response.status_code == 400  # Business Rule verletzt
```

---

### Konzept 39 — pytest Coverage

```bash
pytest test_screens.py -v --cov=routers.screens --cov-report=term-missing
pytest -v  # alle Tests auf einmal
```

- Punkt-Notation für Module: `routers.screens` nicht `routers/screens`
- `term-missing` zeigt welche Zeilen nicht getestet werden
- 100% Coverage bedeutet: jede Zeile wird von mindestens einem Test ausgeführt
- Coverage als Hinweis — nicht als Selbstzweck. Fehlende Coverage zeigt untesteten Code.

---

### Konzept 40 — engine.dispose() für saubere Test-Teardown

```python
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite://", ...)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)
    engine.dispose()  # ← schließt alle Verbindungen sauber
```

Verhindert `ResourceWarning: unclosed database` nach Tests.

---

### Nächste Themen

- **Auth mit FastAPI** — OAuth2, JWT Tokens, Rollen
- **Booking Model** — Kundenbuchungen
- **Rich** — schönere CLI-Ausgaben
- **Edge Case** — Screen wird unavailable wenn Screenings noch geplant sind

---

## 11.04.2026 — Booking und Customer Model, komplexe Business Rules im Endpoint

### Was war die Aufgabe?

`Customer` und `Booking` Models bauen, Buchungscode generieren, Business Rules im Endpoint umsetzen.

---

### Konzept 41 — Models sind DTOs

Pydantic/SQLModel Models sind das Python-Äquivalent von DTOs (Data Transfer Objects):

- `CustomerCreate` → Input DTO (was reinkommt)
- `Customer` → Entity (was in der DB liegt)
- `CustomerPatch` → Patch DTO (was geändert werden darf)

Der Unterschied zu Java: Pydantic übernimmt Validierung und Serialisierung automatisch — keine extra Mapper-Klassen nötig.

---

### Konzept 42 — Separation of Concerns: Model vs. Endpoint

**Model-Validator** — prüft nur was das Objekt selbst weiß:

```python
@field_validator("seats")
@classmethod
def validate_seats(cls, value):
    if value < 1:
        raise ValueError("A booking must be for at least one seat.")
    return value
```

**Endpoint** — prüft Business Rules die mehrere Objekte betreffen:

```python
remaining = screen.capacity - screening.bookings
if booking.seats > remaining:
    raise HTTPException(status_code=400, detail=f"Only {remaining} seats available")
```

Das Model kennt sich selbst — der Endpoint kennt den Kontext.

---

### Konzept 43 — Early Return Pattern

`raise` bricht die Funktion sofort ab — genau wie `return`. Kein `else` nötig:

```python
customer = session.get(Customer, id)
if customer is None:
    raise HTTPException(status_code=404, ...)  # ← bricht ab

# hier sind wir nur wenn customer existiert
session.delete(customer)
session.commit()
return customer
```

Fehlerfall zuerst abhandeln — Happy Path bleibt flach und lesbar.

---

### Konzept 44 — Booking Code generieren mit func.count()

```python
from sqlalchemy import func
from datetime import date

def generate_booking_code(session) -> str:
    today = date.today()
    count = session.exec(
        select(func.count()).select_from(Booking)
        .where(Booking.booking_code.startswith(f"PMT-{today.strftime('%Y%m%d')}"))
    ).one()
    return f"PMT-{today.strftime('%Y%m%d')}-{count + 1:04d}"
```

- `func.count()` gibt immer eine Zahl zurück — auch `0` wenn keine Zeilen gefunden werden. Kein `try/except` nötig.
- `:04d` formatiert die Zahl immer vierstellig: `0001`, `0042`, `1337`
- `startswith()` auf einer SQLAlchemy-Spalte generiert `LIKE 'PMT-20260411%'` in SQL

**Wichtig:** `booking_code` muss `str` sein, nicht `int` — sonst schlägt `LIKE` auf PostgreSQL fehl.

---

### Konzept 45 — Komplexer POST Endpoint mit mehreren Objekten

Wenn ein Endpoint mehrere Objekte anfassen muss:

```python
@router.post("", status_code=201)
async def create_booking(booking: BookingCreate, session: Session = Depends(get_session)):
    # 1. Abhängige Objekte prüfen
    screening = session.get(Screening, booking.screening_id)
    if screening is None:
        raise HTTPException(status_code=404, ...)

    screen = session.get(Screen, screening.screen_id)
    if screen is None:
        raise HTTPException(status_code=404, ...)

    # 2. Business Rule prüfen
    if screen.capacity < screening.bookings + booking.seats:
        raise HTTPException(status_code=400, ...)

    # 3. Booking anlegen
    booking_data = booking.model_dump()
    booking_data["booking_code"] = generate_booking_code(session)
    new_booking = Booking(**booking_data)
    session.add(new_booking)
    session.commit()
    session.refresh(new_booking)

    # 4. Screening aktualisieren
    screening.sqlmodel_update({"bookings": screening.bookings + booking.seats})
    session.add(screening)
    session.commit()

    return new_booking
```

---

### Konzept 46 — Optional Relationship mit Forward Reference

```python
# booking.py
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from models.customer import Customer

class Booking(BookingCreate, table=True):
    customer: Optional["Customer"] = Relationship(back_populates="bookings")
```

- `Optional["Customer"]` statt `"Customer | None"` — SQLAlchemy kann den ganzen String `"Customer | None"` nicht als Forward Reference auflösen
- `TYPE_CHECKING` verhindert Circular Import zur Laufzeit

---

### Konzept 47 — Tabelle neu erstellen nach Model-Änderung

`create_all` erstellt nur **neue** Tabellen — bestehende werden nicht verändert. Nach einer Model-Änderung (z.B. `int` → `str`) muss die Tabelle manuell gedroppt werden:

```bash
docker exec -it bamboo-postgres psql -U panda -d pmt -c "DROP TABLE booking;"
```

Dann App neu starten — `create_all` erstellt die Tabelle mit dem neuen Schema.

**Für die Zukunft:** Alembic — Datenbank-Migrations-Tool das Änderungen sauber verwaltet ohne Datenverlust. Kommt später.

---

---

## 12.04.2026 — Booking Endpoints und Tests

### Was war die Aufgabe?

PATCH und DELETE für Bookings bauen — mit Business Rules die mehrere Objekte gleichzeitig anfassen. Tests für alle Booking-Endpoints schreiben.

---

### Konzept 48 — YAGNI: You Ain't Gonna Need It

Nicht erreichbarer Code gehört nicht in die Codebase. Wenn ein Codepfad durch Datenbank-Constraints garantiert nie ausgeführt wird — raus damit. Weniger Code ist weniger Wartungsaufwand.

---

### Konzept 49 — Kapazitätsberechnung beim Update

```python
new_bookings = screening.bookings - booking.seats + b_patch.seats
```

Alte Buchung abziehen, neue hinzufügen — in einem Schritt. Funktioniert für Erhöhung und Reduzierung gleichermaßen.

---

### Konzept 50 — Objekte leben nach session.delete() weiter

```python
session.delete(booking)
session.commit()
return booking  # ✅ — booking ist noch im Python-Speicher
```

`session.delete()` + `commit()` löscht das Objekt in der DB — aber das Python-Objekt lebt weiter bis die Funktion endet. Kein `session.refresh()` nach Delete — das würde einen Fehler werfen.

---

### Konzept 51 — f-String nicht vergessen in Tests

```python
client.patch("/bookings/{booking.id}", ...)   # ❌ — String, nicht f-String
client.patch(f"/bookings/{booking.id}", ...)  # ✅ — f-String wertet aus
```

Ohne `f` wird `{booking.id}` als Literal-String übergeben — FastAPI kann das nicht als Integer parsen und gibt `422 Unprocessable Entity` zurück.

---

### Konzept 52 — Screening-Update im Test prüfen

Ein guter Test prüft nicht nur den direkten Response — sondern auch Seiteneffekte:

```python
response = client.patch(f"/bookings/{booking.id}", json={"seats": 5})
assert response.status_code == 200

# Seiteneffekt prüfen: wurde screening.bookings korrekt aktualisiert?
screening = session.get(Screening, booking.screening_id)
assert screening.model_dump(mode="json")["bookings"] == 5
```

---

## 2026-04-12 - Supabase JavaScript API & Typer CLI

### Supabase: Wie die JavaScript API wirklich funktioniert

**Wichtigste Erkenntnis:** Die Supabase JS API ist KEIN SQL, sondern JavaScript, das zu SQL wird!

```javascript
// Das sieht aus wie "erst holen, dann filtern":
const { data, error } = await supabase
  .from('trips')
  .select('*, fahrer:profiles(*, gruppe:groups(*))')
  .eq('fahrer_id', fahrerId)
  .order('datum', { ascending: false });

// Aber es wird zu SQL:
SELECT trips.*, profiles.*, groups.*
FROM trips
LEFT JOIN profiles ON trips.fahrer_id = profiles.id
LEFT JOIN groups ON profiles.group_id = groups.id
WHERE trips.fahrer_id = 'xyz'
ORDER BY trips.datum DESC
```

**→ Die Filterung passiert auf dem SERVER, nur das Ergebnis kommt zurück!**

### Joins sind implizit basierend auf Foreign Keys

Der Join zwischen `profiles` und `groups` funktioniert automatisch, weil in der Datenbank ein Foreign Key definiert ist (z.B. `profiles.group_id → groups.id`). Supabase erkennt diese Beziehung automatisch.

### Virtuelle Spalten erzeugen

```javascript
.select('*, fahrer:profiles(*)')
        //  ^^^^^^
        //  Neuer Name im Ergebnis - existiert nicht in der DB!
```

Das Ergebnis hat eine neue Eigenschaft `fahrer` mit den verknüpften Profil-Daten. Die Original-Spalte `fahrer_id` bleibt auch erhalten.

**Erinnert mich an:** `AddColumns()` in PowerFx (PowerApps) - gleiches Konzept!

### Aggregation auf dem Server

**Schlecht:** Alle Trips holen und in JavaScript summieren

```javascript
const trips = await supabase.from('trips').select('start_km, end_km');
const total = trips.reduce((sum, t) => sum + (t.end_km - t.start_km), 0);
```

**Gut:** PostgreSQL Function erstellen und nur das Ergebnis holen

```sql
CREATE FUNCTION get_total_kilometers() RETURNS numeric AS $$
  SELECT COALESCE(SUM(end_kilometer - start_kilometer), 0) FROM trips;
$$ LANGUAGE sql;
```

```javascript
const { data } = await supabase.rpc('get_total_kilometers');
// data ist nur eine Zahl, keine 1000 Zeilen!
```

### Python/Typer: Bugs gefunden und gefixed

**Bug 1:** `enumerate()` falsch verwendet

```python
# FALSCH - gibt "0 - 0, 1 - 1, 2 - 2" aus:
for i, f in enumerate(valid_floors):  # valid_floors = [0, 1, 2, 3]
    typer.echo(f"{i} - {f}")

# RICHTIG - floors sind schon die Zahlen!
for f in valid_floors:
    typer.echo(f)
```

**Bug 2:** While-Loop mit OR läuft ewig

```python
# FALSCH - immer True!
while is_avail != "j" or is_avail != "J" or is_avail != "n" or is_avail != "N":

# RICHTIG:
while is_avail not in ["j", "J", "n", "N"]:
```

**Schönster Code heute:**

```python
is_avail = typer.prompt("Verfügbar? (J/n)", type=str, default="j")
s_avail = is_avail.lower() == "j"
```

So clean! 😍

### typer.Abort() vs. Wiederholung

- `raise typer.Abort()` → Programm komplett abbrechen
- `while`-Schleife → Eingabe wiederholen bei Fehler

Ich wollte Wiederholung, nicht Abbruch!

### click.prompt() > typer.prompt()

**Problem:** `typer.prompt()` zeigt bei `type=int` den Default nicht an und akzeptiert leere Eingabe nicht.

**Lösung:** `click.prompt()` verwenden (Typer basiert eh auf Click):

```python
import click

s_turn = click.prompt("Turnaround-Zeit (Minuten)", type=int, default=15, show_default=True)
# Zeigt: "Turnaround-Zeit (Minuten) [15]:"
# Enter → s_turn = 15 ✅
```

### Nächste Schritte

- PMT CLI weiter ausbauen
- Mehr über PostgreSQL Functions lernen
- Supabase Realtime anschauen?

## 17.04.2026 — Rich Tabellen, CLI Struktur und List Commands

### Was war die Aufgabe?

CLI in Module aufteilen, alle List-Commands mit Rich-Tabellen bauen.

---

### Konzept 53 — CLI Module mit Typer

```python
# cli.py (Projektroot)
from cli import movies, screens, directors

app = typer.Typer()
app.add_typer(movies.app, name="movies")
app.add_typer(screens.app, name="screens")
app.add_typer(directors.app, name="directors")
```

Jedes Modul hat seine eigene `app`:

```python
# cli/movies.py
app = typer.Typer()

@app.command()
def create():
    ...

@app.command()
def list():
    ...
```

Aufruf: `python3 cli.py movies create` statt `python3 cli.py create-movie`

---

### Konzept 54 — Rich Tabellen

```python
from rich.console import Console
from rich.table import Table

console = Console()
table = Table(title="Säle")
table.add_column("Nummer")
table.add_column("Kapazität")

for s in screens:
    table.add_row(str(s.number), str(s.capacity))  # ← immer str!

console.print(table)
```

- `Console` ersetzt `typer.echo()`
- `Table` ist wie `<table>` in HTML — `add_column` wie `<th>`, `add_row` wie `<tr>`
- Alle Werte müssen `str` sein — `str(s.number)` nicht vergessen

---

### Konzept 55 — Mehrere Joins in einer Query

```python
statement = (
    select(Booking, Screening, Movie, Screen)
    .join(Screening, Booking.screening_id == Screening.id)  # type: ignore
    .join(Movie, Screening.movie_id == Movie.id)            # type: ignore
    .join(Screen, Screening.screen_id == Screen.id)         # type: ignore
    .outerjoin(Customer, Booking.customer_id == Customer.id) # type: ignore
)
for booking, screening, movie, screen in results:
    ...
```

- `.join()` für Pflichtbeziehungen
- `.outerjoin()` für optionale Beziehungen (z.B. Customer)
- `# type: ignore` wegen IDE-Warnung — zur Laufzeit korrekt

---

### Konzept 56 — PostgreSQL Sequenzen zurücksetzen

Nach `DELETE` vergibt PostgreSQL keine IDs von 1 neu — die Sequenz läuft weiter. Für den Seed:

```python
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text("ALTER SEQUENCE screening_id_seq RESTART WITH 1"))
    conn.commit()
```

`engine.connect()` direkt für raw SQL — kein SQLModel-Wrapper.

---

### Nächste Themen

- **create-screening** und **create-booking** CLI Commands
- **pyproject.toml** — `pmt` als installierbares CLI
- **Auth mit FastAPI**
