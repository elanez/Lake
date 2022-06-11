class Settings:
    def __init__(self, filename):
        self.filename = filename
    
    def generate_test_settings(self, max_step, model_folder, version, sumo_file):
        with open(self.filename, "w") as settings:
            print('''[agent]\ninput_dim = 16''', file=settings)
            print('''\n[simulation]\nsumo_gui = True''', file=settings)
            print(f'''max_step = {max_step}''', file=settings)
            print('''green_duration = 10''', file=settings)
            print('''yellow_duration = 5''', file=settings)
            print(f'''\n[dir]\nmodel_folder = {model_folder}{version}''', file=settings)
            if model_folder == 'Roxas':
                print(f'''sumo_file = {model_folder}/All/{model_folder}''', file=settings)
            else:
                print(f'''sumo_file = {sumo_file}''', file=settings)
