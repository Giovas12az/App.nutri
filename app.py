from flask import Flask, render_template, url_for, request, redirect, flash, session
import requests


API_KEY = "sLOQcyN5wjjcoLFfb9y7p7Drc5Yp6kotwn8yF9XR"

SP_KEY = "77e84be7e9254bd0914f0a215ccbfe44"  

MAPA_DIETAS = {
    "vegano": "vegan",
    "sin gluten": "gluten free",
    "todas": "",
}

Usuarios_Registrados = {
    "24308060610078@cetis61.edu.mx": {
        "password": "12345678",
        "nombre": "Gio"
    }
}


TRADUCCIONES = {
    "Energy": "Energía",
    "Protein": "Proteína",
    "Total lipid (fat)": "Grasa total",
    "Carbohydrate, by difference": "Carbohidratos",
    "Fiber, total dietary": "Fibra dietética",
    "Sugars, total including NLEA": "Azúcares",
    "Calcium, Ca": "Calcio",
    "Iron, Fe": "Hierro",
    "Sodium, Na": "Sodio",
    "Vitamin C, total ascorbic acid": "Vitamina C",
    "Vitamin D (D2 + D3)": "Vitamina D",
    "Potassium, K": "Potasio",
}

# FUNCIONES DEL ANALIZADOR

#separa cada línea en un ingrediente válido.
def limpiar_ingredientes(texto):
    #divide el texto por saltos de línea
    lineas = texto.split("\n")
    ingredientes = [l.strip() for l in lineas if len(l.strip()) > 2]
    return ingredientes

# identifica cantidad y nombre de cada ingrediente.
def extraer_ingrediente(linea):
    linea = linea.lower().strip()
    partes = linea.split()

    if partes[0].isdigit():
        cantidad = int(partes[0])

        if len(partes) > 1 and partes[1] in ["g", "gr", "gramos", "gramo"]:
            ingrediente = " ".join(partes[2:])
            return cantidad, ingrediente

        if "g" in partes[0]:
            cantidad = int(partes[0].replace("g", "").replace("gr", ""))
            ingrediente = " ".join(partes[1:])
            return cantidad, ingrediente

        ingrediente = " ".join(partes[1:])
        return cantidad, ingrediente

    return 100, linea

# consulta la API de USDA y devuelve nutrientes traducidos.
def buscar_nutrientes(nombre, gramos=100):
    url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {"query": nombre, "api_key": API_KEY}

    res = requests.get(url, params=params).json()

    if "foods" not in res or len(res["foods"]) == 0:
        return None

    alimento = res["foods"][0]
    nutrientes = {}

    factor = gramos / 100  

    for n in alimento.get("foodNutrients", []):
        nombre_nutr = n.get("nutrientName")
        valor = n.get("value")

        if nombre_nutr in TRADUCCIONES:
            nutrientes[TRADUCCIONES[nombre_nutr]] = round(valor * factor, 2)

    return nutrientes




# NUEVA FUNCIÓN: RECETAS SPOONACULAR


def buscar_recetas_api(query, number=6):
    url = "https://api.spoonacular.com/recipes/complexSearch"

    params = {
        "apiKey": SP_KEY,
        "query": query,
        "number": number,
        "addRecipeInformation": True
    }

    res = requests.get(url, params=params).json()

    return res.get("results", [])
#La cadena URL junto con los parámetros indica a la API qué información queremos. 
# Las respuestas se reciben en JSON y se procesan en Python."




# CONFIG FLASK

app = Flask(__name__)
app.secret_key = '2423415414'






# LOGIN / REGISTRO


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombres = request.form.get('nombre')
        apellido = request.form.get('apellido')
        email = request.form.get('email')
        contraseña = request.form.get('password')
        confirmarcontraseña = request.form.get('confirm')
        
        if contraseña != confirmarcontraseña:
            flash("Las contraseñas no coinciden.", "error")
            return redirect(url_for('registro'))
        
        if email in Usuarios_Registrados:
            flash("Este email ya está registrado.", "error")
            return redirect(url_for('registro'))

        Usuarios_Registrados[email] = {
            'nombre': '' + nombres,
            'password': contraseña,
        }

        flash("Registro exitoso. Ahora puedes iniciar sesión.", "success")
        return redirect(url_for('inicio'))

    return render_template('registro.html')


@app.route('/Validalogin', methods=['POST'])
def Validalogin():
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')

    if not email or not password:
        flash('Por favor ingresa email y contraseña', 'error')
        return redirect(url_for('inicio'))

    if email in Usuarios_Registrados:
        usuario = Usuarios_Registrados[email]
        if usuario['password'] == password:
            session['usuario_email'] = email
            session['usuario'] = usuario['nombre']
            session['logueado'] = True
            flash(f'Bienvenido {usuario["nombre"]}', 'success')
            return redirect(url_for('base'))
        else:
            flash('Contraseña incorrecta', 'error')
    else:
        flash('Usuario no encontrado', 'error')

    return redirect(url_for('iniciar_se'))


@app.route('/logout')
def logout():
    session.clear()
    flash(f'Has cerrado sesión correctamente', 'info')
    return redirect(url_for('iniciar_se'))



# PAGINAS


@app.route('/')
def base():
    return render_template('inicio.html')

@app.route('/iniciar_se')
def iniciar_se():
    return render_template('iniciar_se.html')

@app.route('/RD')
def RD():
    return render_template('RD.html')

@app.route('/Educacion')
def Educacion():
    
    return render_template('Educacion.html')


# ANALIZADOR DE RECETAS


@app.route('/Analizador', methods=['GET', 'POST'])
def Analizador():
    resultado_total = {}

    if request.method == 'POST':
        receta = request.form.get("receta", "").strip()

        if not receta:
            flash("Ingresa una receta o lista de ingredientes.", "danger")
            return render_template('Analizador.html')

        ingredientes = limpiar_ingredientes(receta)
        suma = {}

        for ing in ingredientes:
            gramos, nombre_ing = extraer_ingrediente(ing)

            if nombre_ing == "":
                nombre_ing = ing

            datos = buscar_nutrientes(nombre_ing, gramos)

            if datos:
                for k, v in datos.items():
                    suma[k] = suma.get(k, 0) + v

        resultado_total = suma

    return render_template('Analizador.html', resultado=resultado_total)




# INDICE DE MASA CORPORAL

@app.route('/IMC', methods=['GET', 'POST'])
def IMC():
    resultado = None
    categoria = None

    if request.method == 'POST':
        try:
            peso = float(request.form.get('peso'))
            altura = float(request.form.get('altura')) / 100
            imc = peso / (altura ** 2)
            imc = round(imc, 2)

            if imc < 18.5:
                categoria = "Bajo peso"
            elif 18.5 <= imc < 25:
                categoria = "Peso normal"
            elif 25 <= imc < 30:
                categoria = "Sobrepeso"
            else:
                categoria = "Obesidad"

            resultado = imc

        except:
            flash("Por favor ingresa valores válidos", "error")

    return render_template('IMC.html', resultado=resultado, categoria=categoria)



# TASA METABÓLICA BASAL

@app.route('/TMB', methods=['GET', 'POST'])
def TMB():
    tmb = None
    gct = None

    if request.method == 'POST' :
        try:
            peso = float(request.form.get('peso'))
            altura = float(request.form.get('altura'))
            edad = int(request.form.get('edad'))
            genero = request.form.get('genero')
            actividad = float(request.form.get('actividad'))

            if genero == "Hombre":
                tmb = (10 * peso) + (6.25 * altura) - (5 * edad) + 5
            else:
                tmb = (10 * peso) + (6.25 * altura) - (5 * edad) - 161

            tmb = round(tmb, 2)

            gct = round(tmb * actividad, 2)

        except:
            flash("Por favor ingresa valores válidos.", "error")

    return render_template('TMB.html', tmb=tmb, gct=gct)


# PESO CORPORAL IDEAL

@app.route('/PCI', methods=['GET', 'POST'])
def PCI():
    peso_ideal = None

    if request.method == 'POST':
        try:
            altura = float(request.form.get('altura'))
            genero = request.form.get('genero')

            if genero == "Hombre":
                peso_ideal = 50 + 0.9 * (altura - 152)
            else:
                peso_ideal = 45.5 + 0.9 * (altura - 152)

            peso_ideal = round(peso_ideal, 2)

        except:
            flash("Por favor ingresa valores válidos.", "error")

    return render_template('PCI.html', peso_ideal=peso_ideal)



# MACRONUTRIENTES

@app.route('/macronutrientes', methods=['GET', 'POST'])
def macronutrientes():
    calorias = None
    carbohidratos = None
    proteinas = None
    grasas = None

    if request.method == 'POST':
        try:
            calorias = float(request.form.get('calorias'))

            carbohidratos = round((0.50 * calorias) / 4, 2)
            proteinas = round((0.20 * calorias) / 4, 2)
            grasas = round((0.30 * calorias) / 9, 2)

        except:
            flash("Por favor ingresa un valor válido de calorías.", "error")

    return render_template('macronutrientes.html',
                            calorias=calorias,
                            carbohidratos=carbohidratos,
                            proteinas=proteinas,
                            grasas=grasas)



# RECETAS CON SPOONACULAR

# RECETAS CON SPOONACULAR SIMPLIFICADAS (SIN CALORÍAS NI NUTRIENTES)
@app.route("/recetas", methods=["GET", "POST"])
def recetas():
    recetas = []

    if request.method == "POST":
        ingrediente = request.form.get("ingrediente", "")
        tiempo_max = request.form.get("tiempo", "")
        dificultad = request.form.get("dificultad", "")
        dieta = request.form.get("dieta", "")
        calorias = request.form.get("calorias", "")
        tipo = request.form.get("tipo", "")

        # 1 CONSULTA PRINCIPAL A SPOONACULAR
        url_busqueda = "https://api.spoonacular.com/recipes/complexSearch"
        params = {
            "apiKey": SP_KEY,
            "includeIngredients": ingrediente,  # <- Cambio aquí
            "number": 10,
            "addRecipeInformation": True,
        }

        # Filtros opcionales
        if tiempo_max:
            params["maxReadyTime"] = tiempo_max
        if dieta and dieta != "todas":
            params["diet"] = MAPA_DIETAS.get(dieta, "")
        if calorias:
            params["maxCalories"] = calorias

        respuesta = requests.get(url_busqueda, params=params).json()

        # 2 PROCESAR CADA RECETA 
        for r in respuesta.get("results", []):
            receta_id = r["id"]

            # 2 Obtener ingredientes
            ingredientes = [i["original"] for i in r.get("extendedIngredients", [])]

            # 2 Descripción / resumen
            descripcion = r.get("summary", "").replace("<b>", "").replace("</b>", "")

            # 3 Calorías
            calorias_valor = r.get("nutrition", {}).get("nutrients", [{}])[0].get("amount", "No disponible")

            # 4 Dificultad (estimada por tiempo)
            if r.get("readyInMinutes", 0) <= 15:
                dificultad_calc = "Fácil"
            elif r.get("readyInMinutes", 0) <= 30:
                dificultad_calc = "Media"
            else:
                dificultad_calc = "Difícil"

            # 3 OBTENER PASOS DETALLADOS 
            detalle = requests.get(
                f"https://api.spoonacular.com/recipes/{receta_id}/information?apiKey={SP_KEY}"
            ).json()

            pasos = []
            instrucciones = detalle.get("analyzedInstructions", [])

            if instrucciones:
                for paso in instrucciones[0].get("steps", []):
                    pasos.append(paso["step"])

            # 4 AGREGAR RECETA COMPLETA 
            recetas.append({
                "nombre": r.get("title"),
                "imagen": r.get("image"),
                "tiempo": r.get("readyInMinutes"),
                "ingredientes": ingredientes,
                "descripcion": descripcion,
                "dificultad": dificultad_calc,
                "calorias": calorias_valor,
                "pasos": pasos
            })

    return render_template("recetas.html", recetas=recetas)




@app.route('/etiquetas')
def etiquetas():
    return render_template('etiquetas.html')



@app.route('/mitos')
def mitos():
    return render_template('mitos.html')

@app.route('/guia')
def guia():
    return render_template('guia.html')

@app.route('/hidratacion')
def hidratacion():
    return render_template('hidratacion.html')




if __name__ == '__main__':
    app.run(debug=True)
