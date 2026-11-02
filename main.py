import json
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

with open("data/potions.json", "r") as data:
    potions: dict = json.load(data)

def output_potions(values: list[str]):
	input = []
	warning = []
	for val in values:
		if val.strip() == "":
			continue
		if val not in potions:
			warning.append(val)
		elif val != "Select an Effect" and val not in input:
			input.append(val)

	warning_message = (
		"The following effects were not found: " + ", ".join(warning)
		if warning else None
	)

	if not input:
		return None, warning_message

	possible_items = {}
	item_levels = [{} for _ in input]
	for effect in input:
		for ingredient in potions[effect]:
			if ingredient in possible_items:
				possible_items[ingredient][0] += 1
				possible_items[ingredient][1] += " + " + effect
			else:
				possible_items[ingredient] = [1, effect]

	for ingredient, (matches, effects) in possible_items.items():
		level = len(input) - matches
		item_levels[level].setdefault(effects, []).append(ingredient)

	results = []
	for index, category in enumerate(item_levels):
		if not category:
			continue
		matching_effects = len(input) - index
		count = "All" if index == 0 and len(input) != 1 else str(matching_effects)
		results.append({
			"heading": f"Items Matching {count} Effect{'s' if matching_effects != 1 else ''}",
			"groups": [
				{"effects": effects, "ingredients": items}
				for effects, items in category.items()
			]
		})

	return results, warning_message

def get_query_params(request: Request):
	return [
		request.query_params.get(f"I{number}", "")
		for number in range(1, 5)
	]

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="views")

@app.get("/", response_class=HTMLResponse)
async def ret_main(request: Request):
	selected_effects = get_query_params(request)
	out = output_potions(selected_effects)
	selections = []
	for effect in potions:
		selected_by = next(
			(number for number, selected in enumerate(selected_effects, start=1)
			 if effect == selected),
			0,
		)
		selections.append({"value": effect, "selected": selected_by})

	return templates.TemplateResponse(
		request=request, name="main.html", context={
			"Warn": out[1],
			"Output": out[0],
			"Selections": selections,
		}
	)

@app.get("/data")
async def ret_json(request: Request):
	selected_effects = get_query_params(request)
	hasValues = False
	for effect in selected_effects:
		if (effect != ""):
			hasValues = True
			break
	if hasValues:
		out = output_potions(selected_effects)
		return JSONResponse(
			content={
				"Warn": out[1],
				"Output": out[0],
			}, 
			status_code=200
		)
	else:
		return JSONResponse(content=potions, status_code=200)