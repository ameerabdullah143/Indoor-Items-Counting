
import json
import cv2
import numpy as np


donation_zones_path = 'ADC-RIVER.OAKS-MACO2.jpg.json'
data_path = 'h264__2023-09-03_15-18-01-ADC-RIVER.OAKS-MACO2_09042023.json'

def get_donation_zones(path):
    # Opening JSON file
    f = open(path)
    
    # returns JSON object as
    # a dictionary
    data = json.load(f)
    
    donation_zones = []
    for i in data['instances']:
        print(i)
        p = np.array(i['points']).astype(int)
        p = np.reshape(p,((p.shape[0])//2,2))
        if i['className']=='DonationZone':
          donation_zones.append(p)
    
        # cv2.polylines(img, [p], True, (255,0,0),3)
    global height
    global width
    height,width = data['metadata']['height'],data['metadata']['width']
    
    
    # Closing file=
    f.close()
    
    return donation_zones

def parse_string(s):
  items = s.split('|')

  cls, t_id, _, x1_p, y1_p, x2_p, y2_p, conf = items

  x1, y1 = int(int(x1_p) * width / 10000), int(int(y1_p) * height / 10000)
  x2, y2 = int(int(x2_p) * width / 10000), int(int(y2_p) * height / 10000)

  cx = int((x1+x2)/2)
  cy = int((y1+y2)/2)

  return cls,int(t_id),x1,y1,cx,cy,float(conf) 

def update_counter(counted_items,arm_items):
    c = 0
    for key,item in arm_items.items():        
        if (cv2.pointPolygonTest(donation_zones[0], item[0],False)==-1 and
            (cv2.pointPolygonTest(donation_zones[0], item[1],False)==1 or
             cv2.pointPolygonTest(donation_zones[1], item[1],False)==1)):
            
            counted_items.add(key)
            
        else:
            counted_items.discard(key)


donation_zones = get_donation_zones(donation_zones_path)



# Opening JSON file
f = open(data_path)

# returns JSON object as
    # a dictionary
data = json.load(f)['messages']


arm_items = {}
counted_items = set()
i = 0
for frame in data:
    
  # processing each frame
  for i in frame['objects']:
      
        obj = parse_string(i)
        if obj[0]== 'Arm_Item':
            if obj[1] in arm_items:
                arm_items[obj[1]] = [arm_items[obj[1]][0],(obj[4],obj[5])]

            else:
                arm_items[obj[1]] = [(obj[4],obj[5]),(obj[4],obj[5])]
            
       
  update_counter(counted_items, arm_items)
  
              

  # print(len(counted_items))
  

print("Total items:",4)
    
