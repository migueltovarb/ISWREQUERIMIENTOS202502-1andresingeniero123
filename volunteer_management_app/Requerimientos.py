PRODUCTOS = {}

def agregar_producto():
    nombre = input("Ingrese nombre del nuevo producto: ")
    precio = float(input("Ingrese precio del producto: "))
    PRODUCTOS[nombre] = precio
    print(f"Producto {nombre} agregado con precio ${precio}")

def MostrarMenu():
    print("\n--- Menú de Productos ---")
    if not PRODUCTOS:
        print("No hay productos en el menú. Agregue algunos primero.")
    else:
        for item, price in PRODUCTOS.items():
            print(f"{item}: ${price}")


def AgregarProducto(orden, producto, cantidad):
    if producto in PRODUCTOS:
        orden[producto] = orden.get(producto, 0) + cantidad
        print(f"Agregado {cantidad} x {producto}")
    else:
        print("Producto no existe. Agreguelo primero al menú.")


def QuitarProducto(orden, producto, cantidad):
    if producto in orden:
        if orden[producto] <= cantidad:
            orden.pop(producto)
            print(f"{producto} removido del pedido.")
        else:
            orden[producto] -= cantidad
            print(f"Removido {cantidad} x {producto} del pedido.")
    else:
        print("Producto no se encuentra en el pedido.")


def CalcularTotal(orden):
    total = sum(PRODUCTOS[producto] * cantidad for producto, cantidad in orden.items())
    return total


def aplicar_descuento(total, tiene_carne):
    if tiene_carne:
        descuento = total * 0.1
        return total - descuento
    return total


def facturar(orden, tiene_carne):
    total = CalcularTotal(orden)
    total_final = aplicar_descuento(total, tiene_carne)
    print("\n--- Factura ---")
    for producto, cantidad in orden.items():
        print(f"{producto} x {cantidad} = ${PRODUCTOS[producto] * cantidad}")
    if tiene_carne:
        print("Descuento aplicado: 10%")
    print(f"Total a pagar: ${total_final}")


def guardar_pedido(orden):
    try:
        with open("pedido.txt", "w") as f:
            for producto, cantidad in orden.items():
                f.write(f"{producto}: {cantidad}\n")
        print("Pedido guardado exitosamente.")
    except:
        print("Error al guardar el pedido")


def main():
    orden = {}
    pasos = 0
    print("Bienvenido a Cafetería Campus - Sistema de Pedidos")
    
    while pasos < 4:
        MostrarMenu()
        accion = input("\nElija una acción (agregar_producto, agregar, eliminar, facturar, salir): ").strip().lower()
        
        if accion == "agregar_producto":
            agregar_producto()
        elif accion == "agregar":
            producto = input("Ingrese el nombre del producto: ")
            cantidad = int(input("Ingrese la cantidad: "))
            AgregarProducto(orden, producto, cantidad)
        elif accion == "eliminar":
            producto = input("Ingrese el nombre del producto a quitar: ")
            cantidad = int(input("Ingrese la cantidad a quitar: "))
            QuitarProducto(orden, producto, cantidad)
        elif accion == "facturar":
            tiene_carne = input("¿Posee carné válido para descuento? (s/n): ").strip().lower() == "s"
            facturar(orden, tiene_carne)
            guardar_pedido(orden)
            break
        elif accion == "salir":
            print("Saliendo del sistema.")
            break
        else:
            print("Acción no válida. Intente de nuevo.")
            
        pasos += 1
    else:
            print("Máximo de pasos alcanzado. Facturando automáticamente...")
    tiene_carne = False
    facturar(orden, tiene_carne)
    guardar_pedido(orden)
if __name__ == "__main__":
    main()
