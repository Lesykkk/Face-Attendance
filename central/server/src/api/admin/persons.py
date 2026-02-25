from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, delete, update
from sqlalchemy.exc import IntegrityError

from core.dependencies import AdminDep, DbDep
from models.person import Person
from models.face_embedding import FaceEmbedding
from schemas.person import PersonRegister, PersonResponse, PersonUpdate
from services.embedding_service import extract_embedding_from_base64, MultipleFacesError, NoFaceError

router = APIRouter(prefix="/persons", tags=["Persons"])



@router.get("", response_model=list[PersonResponse])
async def get_persons(db: DbDep, _admin: AdminDep):
    result = await db.execute(
        select(Person).order_by(Person.role, Person.full_name)
    )
    return result.scalars().all()


@router.post("", response_model=PersonResponse, status_code=status.HTTP_201_CREATED)
async def register_person(body: PersonRegister, db: DbDep, _admin: AdminDep):
    person = Person(**body.model_dump(exclude={"photos"}))
    db.add(person)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, f"Person code '{body.person_code}' already exists")

    embeddings_created = 0
    try:
        for idx, photo_b64 in enumerate(body.photos, start=1):
            try:
                embedding = extract_embedding_from_base64(photo_b64)
            except MultipleFacesError:
                await db.rollback()
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    f"Photo №{idx} contains more than one face. Each photo must have exactly one face.",
                )
            except NoFaceError:
                await db.rollback()
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    f"Photo №{idx} does not contain a face.",
                )

            fe = FaceEmbedding(person_id=person.id, embedding=embedding)
            db.add(fe)
            embeddings_created += 1

        await db.commit()
    except Exception:
        await db.rollback()
        raise

    return PersonResponse(
        id=person.id,
        full_name=person.full_name,
        person_code=person.person_code,
        role=person.role,
        embeddings_count=embeddings_created,
    )


@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_person(person_id: int, db: DbDep, _admin: AdminDep):
    try:
        result = await db.execute(delete(Person).where(Person.id == person_id))
        if result.rowcount == 0:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Person not found")
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Person is used by other entities")


@router.patch("/{person_id}", response_model=PersonResponse)
async def update_person(person_id: int, body: PersonUpdate, db: DbDep, _admin: AdminDep):
    data = body.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "No fields to update")
    try:
        result = await db.execute(
            update(Person)
            .where(Person.id == person_id)
            .values(**data)
            .returning(Person)
        )
        person = result.scalar_one_or_none()
        if person is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Person not found")
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Person already exists")
    
    return person