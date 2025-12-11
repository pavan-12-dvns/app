import streamlit as st
from PIL import Image
import io

st.set_page_config(page_title="Smart Wellness Assistant", layout="centered")

# -------------------------
# SMALL FOOD DATABASE (per 100g)
# Add more items if you want
# -------------------------
FOOD_DB = {
    "Rice (100g)": {"cal": 130, "protein": 2.7, "carbs": 28, "fat": 0.3},
    "Roti (100g)": {"cal": 120, "protein": 3.0, "carbs": 20, "fat": 3.0},
    "Chicken Breast (100g)": {"cal": 165, "protein": 31, "carbs": 0, "fat": 3.6},
    "Egg (100g)": {"cal": 155, "protein": 13, "carbs": 1.1, "fat": 11},
    "Oats (100g)": {"cal": 389, "protein": 17, "carbs": 66, "fat": 7},
    "Paneer (100g)": {"cal": 265, "protein": 18, "carbs": 6, "fat": 20},
    "Banana (100g)": {"cal": 89, "protein": 1.1, "carbs": 23, "fat": 0.3},
    "Milk (100ml)": {"cal": 60, "protein": 3.2, "carbs": 5, "fat": 3.5},
    "Almonds (100g)": {"cal": 579, "protein": 21, "carbs": 22, "fat": 50},
    "Broccoli (100g)": {"cal": 34, "protein": 2.8, "carbs": 6.6, "fat": 0.4},
}

# -------------------------
# Helper functions
# -------------------------
def calc_nutrients(food_key, grams):
    info = FOOD_DB[food_key]
    factor = grams / 100.0
    return {
        "cal": info["cal"] * factor,
        "protein": info["protein"] * factor,
        "carbs": info["carbs"] * factor,
        "fat": info["fat"] * factor,
    }

def mifflin_bmr(weight_kg, height_cm, age, gender):
    if gender.lower().startswith("m"):
        return 10*weight_kg + 6.25*height_cm - 5*age + 5
    else:
        return 10*weight_kg + 6.25*height_cm - 5*age - 161

def activity_factor(choice):
    mapping = {
        "Sedentary": 1.2,
        "Light (1-3x/wk)": 1.375,
        "Moderate (3-5x/wk)": 1.55,
        "Active (6-7x/wk)": 1.725,
        "Very active / labor": 1.9
    }
    return mapping.get(choice, 1.2)

def goal_calories(tdee, goal):
    if goal == "Lose weight":
        return tdee * 0.85
    elif goal == "Gain weight":
        return tdee * 1.15
    else:
        return tdee

def macro_targets(calories_target, weight_kg, protein_g_per_kg=1.6, fat_percent=0.25):
    protein_g = protein_g_per_kg * weight_kg
    fat_cal = fat_percent * calories_target
    fat_g = fat_cal / 9.0
    protein_cal = protein_g * 4.0
    carb_cal = calories_target - (protein_cal + fat_cal)
    carb_g = max(0.0, carb_cal / 4.0)
    return {"calories": calories_target, "protein_g": protein_g, "fat_g": fat_g, "carb_g": carb_g}

# -------------------------
# UI
# -------------------------
st.title("💚 sMart Wellness Recommendation Assistant")

tabs = st.tabs(["Home", "Food Gallery", "Personal Details", "Diet Recommendation"])

# --- Home tab ---
with tabs[0]:
    st.header("Welcome!")
    st.write("This app helps you: 1) calculate calories & macros for foods, 2) track daily intake, 3) get an automatic diet plan based on your details.")
    st.write("Use *Food Gallery* to add eaten items. Then enter your personal details and open *Diet Recommendation* to get a plan.")

# --- Food Gallery tab ---
with tabs[1]:
    st.header("Food Gallery & Macro Calculator")
    col1, col2 = st.columns([2,1])
    with col1:
        food_choice = st.selectbox("Select food (per 100g values)", list(FOOD_DB.keys()))
        grams = st.number_input("Enter grams consumed", min_value=1, value=100)
        if st.button("Add to daily intake"):
            item_n = calc_nutrients(food_choice, grams)
            # store in session state
            if "intake" not in st.session_state:
                st.session_state.intake = []
            st.session_state.intake.append({"food": food_choice, "grams": grams, **item_n})
            st.success(f"Added {grams}g of {food_choice}")
    with col2:
        st.subheader("Per 100g")
        info = FOOD_DB[food_choice]
        st.write(f"Calories: {info['cal']} kcal")
        st.write(f"Protein: {info['protein']} g")
        st.write(f"Carbs: {info['carbs']} g")
        st.write(f"Fat: {info['fat']} g")
    st.markdown("---")
    st.subheader("Today's entries")
    if "intake" in st.session_state and st.session_state.intake:
        total = {"cal":0,"protein":0,"carbs":0,"fat":0}
        for e in st.session_state.intake:
            st.write(f"- {e['food']} • {e['grams']}g  →  {e['cal']:.1f} kcal, P:{e['protein']:.1f}g, C:{e['carbs']:.1f}g, F:{e['fat']:.1f}g")
            for k in total:
                total[k] += e[k]
        st.write("*Daily totals:*")
        st.write(f"Calories: {total['cal']:.1f} kcal | Protein: {total['protein']:.1f} g | Carbs: {total['carbs']:.1f} g | Fat: {total['fat']:.1f} g")
    else:
        st.info("No foods added yet. Add items above to track intake.")

# --- Personal details tab ---
with tabs[2]:
    st.header("Personal Details (used to generate plan)")
    with st.form("personal_form"):
        name = st.text_input("Name (optional)")
        age = st.number_input("Age", min_value=10, max_value=100, value=20)
        gender = st.selectbox("Gender", ["Male","Female"])
        weight = st.number_input("Weight (kg)", min_value=25.0, max_value=200.0, value=60.0, format="%.1f")
        height = st.number_input("Height (cm)", min_value=120.0, max_value=230.0, value=170.0, format="%.1f")
        activity = st.selectbox("Activity Level", ["Sedentary", "Light (1-3x/wk)", "Moderate (3-5x/wk)", "Active (6-7x/wk)", "Very active / labor"])
        goal = st.selectbox("Goal", ["Maintain weight", "Lose weight", "Gain weight"])
        submitted = st.form_submit_button("Save details")
        if submitted:
            st.session_state.user = {"name": name, "age": age, "gender": gender, "weight": weight, "height": height, "activity": activity, "goal": goal}
            st.success("Details saved!")

# --- Diet recommendation tab ---
with tabs[3]:
    st.header("Diet Recommendation")
    if "user" not in st.session_state:
        st.warning("Please fill your personal details in the 'Personal Details' tab first.")
    else:
        u = st.session_state.user
        st.subheader(f"Hello {u.get('name') or ''} — here is your personalized plan")
        bmr = mifflin_bmr(u['weight'], u['height'], u['age'], u['gender'])
        tdee = bmr * activity_factor(u['activity'])
        target = goal_calories(tdee, "Lose weight" if u['goal']=="Lose weight" else ("Gain weight" if u['goal']=="Gain weight" else "Maintain weight"))
        macros = macro_targets(target, u['weight'])

        st.metric("BMR", f"{int(bmr)} kcal")
        st.metric("TDEE", f"{int(tdee)} kcal")
        st.metric("Target Calories", f"{int(macros['calories'])} kcal")

        st.write(f"Protein target: *{int(macros['protein_g'])} g*  •  Fat target: *{int(macros['fat_g'])} g*  •  Carbs target: *{int(macros['carb_g'])} g*")

        st.markdown("### Suggested meal split (example)")
        st.write("- Breakfast: 25% of daily calories")
        st.write("- Lunch: 35% of daily calories")
        st.write("- Dinner: 30% of daily calories")
        st.write("- Snacks: 10% of daily calories")

        # Simple auto-suggestions (heuristic)
        def simple_meal_suggestions():
            plan = {}
            for meal, frac in [("Breakfast",0.25),("Lunch",0.35),("Dinner",0.30),("Snacks",0.10)]:
                cals = macros['calories'] * frac
                p = macros['protein_g'] * frac
                f = macros['fat_g'] * frac
                c = macros['carb_g'] * frac
                plan[meal] = {"cals": cals, "p": p, "f": f, "c": c}
            return plan

        plan = simple_meal_suggestions()
        for meal, vals in plan.items():
            st.markdown(f"{meal}** — ~{int(vals['cals'])} kcal | P:{int(vals['p'])}g C:{int(vals['c'])}g F:{int(vals['f'])}g")
            # simple textual food suggestions
            if meal == "Breakfast":
                st.write("Suggested: Oats + Milk + 1-2 Eggs + Banana")
            elif meal == "Lunch":
                st.write("Suggested: Rice / Roti + Chicken / Paneer + Salad / Veggies")
            elif meal == "Dinner":
                st.write("Suggested: Roti + Dal + Veggies (lighter)")
            else:
                st.write("Suggested: Fruit, Nuts, Greek yogurt")

        st.info("Note: This is a basic generator for a mini-project. For clinical diet plans consult a nutritionist.")