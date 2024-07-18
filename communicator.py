# communicator.py

class Communicator:
    __frontend_object = None
    __output_format = None  # Add this line to store output format in headless mode

    @classmethod
    def show_message(cls, message):
        if cls.__frontend_object:
            cls.__frontend_object.messageshowing(message)
        else:
            print(message)  # Print message to console in headless mode

    @classmethod
    def show_error_message(cls, message, error_code):
        if cls.__frontend_object:
            message = f"{message} Error code is: {error_code}"
            cls.__frontend_object.messageshowing(message)
        else:
            print(f"Error: {message}, Code: {error_code}")  # Print error message to console in headless mode

    @classmethod
    def set_frontend_object(cls, frontend_object):
        cls.__frontend_object = frontend_object

    @classmethod
    def set_output_format(cls, output_format):
        cls.__output_format = output_format

    @classmethod
    def end_processing(cls):
        if cls.__frontend_object:
            cls.__frontend_object.end_processing()
        else:
            print("Processing ended")  # Print to console in headless mode

    @classmethod
    def get_output_format(cls):
        if cls.__frontend_object:
            return cls.__frontend_object.outputFormatValue
        else:
            return cls.__output_format  # Return the stored output format in headless mode
