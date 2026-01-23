# Catálogo de Recompensas por Puntos
# Este archivo define las recompensas disponibles para canje

CATALOGO_RECOMPENSAS = [
    # --- Sección A: Cupones de Efectivo ---
    {
        'id': 101,
        'nombre': 'Cupón $2',
        'descripcion': 'Ahorra $2 en tu compra. (Mín. compra $5)',
        'costo_puntos': 10,  # Bajado de 15
        'valor': 2.00,
        'tipo': 'DES',
        'icono': '💵',
        'color': '#10b981',
        'seccion': 'efectivo',
        'min_compra': 5.00  # Nueva validación
    },
    {
        'id': 102,
        'nombre': 'Cupón $3',
        'descripcion': 'Ahorra $3 en tu compra. (Mín. compra $5)',
        'costo_puntos': 20,  # Bajado de 25
        'valor': 3.00,
        'tipo': 'DES',
        'icono': '💵',
        'color': '#10b981',
        'seccion': 'efectivo',
        'min_compra': 5.00
    },
    {
        'id': 103,
        'nombre': 'Cupón $5',
        'descripcion': 'Ahorra $5 en tu compra. (Mín. compra $10)',
        'costo_puntos': 30,  # Bajado de 40
        'valor': 5.00,
        'tipo': 'DES',
        'icono': '💵',
        'color': '#10b981',
        'seccion': 'efectivo',
        'min_compra': 10.00
    },
    {
        'id': 104,
        'nombre': 'Cupón $7',
        'descripcion': 'Ahorra $7 en tu compra. (Mín. compra $10)',
        'costo_puntos': 45,  # Bajado de 60
        'valor': 7.00,
        'tipo': 'DES',
        'icono': '💎',
        'color': '#10b981',
        'seccion': 'efectivo',
        'min_compra': 10.00
    },
    {
        'id': 105,
        'nombre': 'Cupón $8',
        'descripcion': 'Ahorra $8 en tu compra. (Mín. compra $10)',
        'costo_puntos': 55,  # Bajado de 70
        'valor': 8.00,
        'tipo': 'DES',
        'icono': '💎',
        'color': '#10b981',
        'seccion': 'efectivo',
        'min_compra': 10.00
    },

    # --- Sección B: Descuentos Porcentuales ---
    {
        'id': 201,
        'nombre': '5% OFF',
        'descripcion': 'Descuento del 5% en el total.',
        'costo_puntos': 30,
        'valor': 5.00,
        'tipo': 'POR',
        'icono': '✂️',
        'color': '#f59e0b',
        'seccion': 'porcentaje',
        'min_compra': 0.00
    },
    {
        'id': 202,
        'nombre': '7% OFF',
        'descripcion': 'Descuento del 7% en el total.',
        'costo_puntos': 50,
        'valor': 7.00,
        'tipo': 'POR',
        'icono': '✂️',
        'color': '#f59e0b',
        'seccion': 'porcentaje',
        'min_compra': 0.00
    },
    {
        'id': 203,
        'nombre': '10% OFF',
        'descripcion': 'Descuento del 10% en el total.',
        'costo_puntos': 75,
        'valor': 10.00,
        'tipo': 'POR',
        'icono': '🔥',
        'color': '#f59e0b',
        'seccion': 'porcentaje',
        'min_compra': 0.00
    },
    {
        'id': 204,
        'nombre': '12% OFF',
        'descripcion': 'Descuento del 12% en el total.',
        'costo_puntos': 100,
        'valor': 12.00,
        'tipo': 'POR',
        'icono': '🔥',
        'color': '#f59e0b',
        'seccion': 'porcentaje',
        'min_compra': 0.00
    },
]
