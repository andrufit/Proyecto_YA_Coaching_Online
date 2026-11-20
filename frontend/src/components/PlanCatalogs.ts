export type CatalogGroup = { id: string; label: string; items: string[] };

// Starter lists: names only. The coach defines loads, quantities, and instructions.
export const exerciseCatalog: CatalogGroup[] = [
  { id: "chest", label: "Pecho", items: ["Press de banca con barra", "Press de banca con mancuernas", "Press inclinado con mancuernas", "Aperturas con mancuernas", "Cruces en polea", "Flexiones de pecho"] },
  { id: "back", label: "Espalda", items: ["Jalón al pecho", "Dominadas", "Remo con barra", "Remo con mancuerna", "Remo en polea baja", "Pullover en polea"] },
  { id: "shoulders", label: "Hombros", items: ["Press militar con barra", "Press de hombros con mancuernas", "Elevaciones laterales", "Elevaciones frontales", "Pájaros con mancuernas", "Face pull"] },
  { id: "biceps", label: "Bíceps", items: ["Curl con barra", "Curl con mancuernas", "Curl martillo", "Curl predicador", "Curl en polea"] },
  { id: "triceps", label: "Tríceps", items: ["Extensión de tríceps en polea", "Extensión de tríceps sobre la cabeza", "Press francés", "Fondos en paralelas", "Press de banca con agarre cerrado"] },
  { id: "quads", label: "Cuádriceps", items: ["Sentadilla con barra", "Sentadilla goblet", "Prensa de piernas", "Extensión de cuádriceps", "Sentadilla búlgara", "Zancadas"] },
  { id: "hamstrings", label: "Isquiotibiales", items: ["Peso muerto rumano", "Curl femoral acostado", "Curl femoral sentado", "Curl femoral de pie", "Buenos días con barra"] },
  { id: "glutes", label: "Glúteos", items: ["Hip thrust", "Puente de glúteos", "Patada de glúteo en polea", "Abducción de cadera en máquina", "Subida al banco"] },
  { id: "calves", label: "Pantorrillas", items: ["Elevación de talones de pie", "Elevación de talones sentado", "Elevación de talones en prensa"] },
  { id: "core", label: "Abdomen y zona media", items: ["Plancha abdominal", "Plancha lateral", "Crunch abdominal", "Elevación de rodillas", "Dead bug", "Press Pallof"] },
  { id: "cardio", label: "Cardio", items: ["Caminata en cinta", "Bicicleta estática", "Elíptica", "Remo ergómetro", "Saltar la cuerda"] },
];

export const foodCatalog: CatalogGroup[] = [
  { id: "proteins", label: "Carnes, pescados y huevos", items: ["Pechuga de pollo", "Carne de res", "Lomo de cerdo", "Pavo", "Atún", "Salmón", "Tilapia", "Huevo entero", "Claras de huevo"] },
  { id: "grains", label: "Cereales y derivados", items: ["Arroz blanco", "Arroz integral", "Avena", "Pasta", "Pan integral", "Pan blanco", "Arepa de maíz", "Quinua", "Granola"] },
  { id: "roots", label: "Tubérculos y plátanos", items: ["Papa", "Batata", "Yuca", "Plátano verde", "Plátano maduro"] },
  { id: "legumes", label: "Legumbres", items: ["Lentejas", "Fríjoles", "Garbanzos", "Arvejas", "Soya"] },
  { id: "dairy", label: "Lácteos y alternativas", items: ["Leche", "Leche deslactosada", "Yogur natural", "Yogur griego", "Queso fresco", "Bebida de soya", "Bebida de almendras", "Tofu"] },
  { id: "fruits", label: "Frutas", items: ["Banano", "Manzana", "Pera", "Mango", "Piña", "Papaya", "Fresa", "Naranja", "Uvas", "Sandía"] },
  { id: "vegetables", label: "Verduras y hortalizas", items: ["Brócoli", "Espinaca", "Lechuga", "Tomate", "Zanahoria", "Pepino", "Calabacín", "Habichuelas", "Pimentón", "Cebolla"] },
  { id: "fats", label: "Aceites, frutos secos y semillas", items: ["Aceite de oliva", "Aguacate", "Almendras", "Maní", "Nueces", "Mantequilla de maní", "Semillas de chía", "Semillas de linaza"] },
];
