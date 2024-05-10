import requests
import json
import argparse
import numpy as np

from PIL import Image  
  
# Opens a image in RGB mode  
im1 = Image.open(r"../2666.jpg")  
#im2 = Image.open(r"../3661.jpg") 
#im3 = Image.open(r"../10835.jpg") 
#im4 = Image.open(r"../15088.jpg") 
#im5 = Image.open(r"../16333.jpg") 
#im1 = im.resize(newsize)
data = json.dumps({
  "inputs": [np.array(im1).tolist()]
#            np.array(im2).tolist(),np.array(im3).tolist(),
#            np.array(im4).tolist(),np.array(im5).tolist()]
})
data = {
    #"project_id": "edustudent360",
    "model_path": "gs://labellerr-models-v1/cl1/prj1/ques1/01",
    "records": [
        {
            #"Image ID": "datasets_111880_269359_seg_pred_seg_pred_10004.jpg",
            "Image URI": "gs://labellerr-models-v1/cl1/prj1/data/5713.jpg",
            #"Height": 150,
            #"Width": 150
        },]
        }
newHeaders = {'Content-type': 'application/json', 'Accept': 'text/plain'}
json_response = requests.post("http://localhost:8080/v1/models/predict", data=json.dumps(data), headers=newHeaders)
import pdb; pdb.set_trace()
print(json_response.json())