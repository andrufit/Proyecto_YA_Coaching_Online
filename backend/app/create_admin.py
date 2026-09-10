from getpass import getpass

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.database import SessionLocal
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.user_service import (
    UserAlreadyExistsError,
    create_user,
)


def main() -> None:
    print("Crear la primera cuenta administradora")
    print()

    with SessionLocal() as db:
        existing_admin = db.scalar(
            select(User).where(User.role == "admin")
        )

        if existing_admin is not None:
            print("Ya existe una cuenta administradora.")
            print("No se creó otra cuenta.")
            return

        email = input("Correo del administrador: ").strip()
        password = getpass("Contraseña (mínimo 8 caracteres): ")
        confirmation = getpass("Confirma la contraseña: ")

        if password != confirmation:
            print("Las contraseñas no coinciden.")
            return

        try:
            user_data = UserCreate(
                email=email,
                password=password,
            )
        except ValidationError as error:
            print("Revisa los datos ingresados:")

            for detail in error.errors():
                field = ".".join(
                    str(part) for part in detail["loc"]
                )
                print(f"- {field}: {detail['msg']}")

            return

        try:
            user = create_user(db, user_data)
        except UserAlreadyExistsError:
            db.rollback()
            print("Ya existe una cuenta con ese correo.")
            print("Usa un correo distinto para el administrador.")
            return
        except IntegrityError:
            db.rollback()
            print("No fue posible crear la cuenta: conflicto de datos.")
            return

        # Reutilizamos el servicio existente para guardar la
        # contraseña con el mismo hash que usa la autenticación.
        user.role = "admin"

        try:
            db.commit()
            db.refresh(user)
        except IntegrityError:
            db.rollback()
            print("La cuenta se creó, pero no se pudo asignar el rol admin.")
            print("Revisa el error antes de volver a ejecutar el comando.")
            return

        print()
        print("Cuenta administradora creada correctamente.")
        print(f"Correo: {user.email}")
        print(f"Rol: {user.role}")


if __name__ == "__main__":
    main()