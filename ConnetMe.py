class contactos: #regitrara contactos, nombre, numeros, correos
   
    contactos = []

def registrar_contacto():
    nombre = input("Nombre: ")
    telefono = input("Teléfono: ")
    correo = input("Correo: ")
    cargo = input("Cargo: ")

    # Valida que solo haya un correo
    for c in contactos:
        if c["correo"] == correo:
            print("Ese correo ya está registrado.\n")
            return

    contacto = {"nombre": nombre, "telefono": telefono, "correo": correo, "cargo": cargo}
    contactos.append(contacto)
    print("Contacto agregado correctamente.\n")

def buscar_contacto():
    dato = input("Ingrese nombre o correo: ")
    for c in contactos:
        if c["nombre"] == dato or c["correo"] == dato:
            print(f"Nombre: {c['nombre']}, Teléfono: {c['telefono']}, Correo: {c['correo']}, Cargo: {c['cargo']}\n")
            return
    print(" No se encontró el contacto.\n")

def eliminar_contacto():
    correo = input("Ingrese el correo del contacto a eliminar: ")
    for c in contactos:
        if c["correo"] == correo:
            contactos.remove(c)
            print("Contacto eliminado.\n")
            return
    print("No se encontró ese contacto.\n")

def listar_contactos():
    if not contactos:
        print("No hay contactos registrados.\n")
    else:
        for c in contactos:
            print(f"{c['nombre']} - {c['telefono']} - {c['correo']} - {c['cargo']}")
        print()

# Menú principal
while True:
    print("---- AGENDADECONTACTOS ----")
    print("1. Registrar contacto")
    print("2. Buscar contacto")
    print("3. Eliminar contacto")
    print("4. Ver todos los contactos")
    print("5. Salir")
    opcion = input("Elija una opción: ")

    if opcion == "1":
        registrar_contacto()
    elif opcion == "2":
        buscar_contacto()
    elif opcion == "3":
        eliminar_contacto()
    elif opcion == "4":
        listar_contactos()
    elif opcion == "5":
        print("Hasta luego!")
        break
    else:
        print("Opción no válida.\n")

