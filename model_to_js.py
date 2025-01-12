import logging
import sys


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    json_file_name = sys.argv[1]

    logging.info(f"Reading model from {json_file_name}")
    with open(json_file_name, 'r') as f:
        model_json = f.read()
    
    text = "const model_data = " + model_json + ";"

    js_file_name = json_file_name.split('.')[0] + '.js'
    logging.info("Writing model to {}".format(js_file_name))
    with open(js_file_name, 'w') as f:
        f.write(text)
