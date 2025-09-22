from NKDatabase.InitialValues.InitialValues import get_config

class Constants:
    def __init__(self, debugging:bool=True, ini_file:str = "database.ini") -> None:

        self.debug_mode = debugging
        self.parameters = get_config('nkInvoice', self.debug_mode)
        #
        ### Read the parameters from the configuration
        #
        

if __name__ == "__main__":
    constants = Constants()
    print(constants.parameters)