def get_student_status(student_id: str):

    fake_database = {
        "1024": "Aceptado en práctica en Lyon",
        "2048": "Pendiente de documentos",
        "3001": "Entrevista programada"
    }

    return fake_database.get(student_id, "Estudiante no encontrado")