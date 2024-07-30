def parse_complex(sub_models: list[str], data: dict) -> dict:
	"""
	prepare data from puerpy.model.Model.get_by_join()
	for BaseModel.model_validate method
	"""
	normalized = {}

	for key, value in data.items():
		splitted_key = key.split('__')
		sub_model    = splitted_key[0]

		if sub_model in sub_models:
			if not normalized.get(sub_model):
				normalized[sub_model] = {}
			normalized[sub_model][splitted_key[1]] = value
		else:
			normalized[key] = value
	
	return normalized

def parse_complex_list(sub_models: list[str], data: list[dict]) -> list[dict]:
	"""
	prepare data from puerpy.model.Model.get_all_join()
	for RootModel[list[BaseModel]].model_validate method
	"""
	return [parse_complex(sub_models, d) for d in data]
