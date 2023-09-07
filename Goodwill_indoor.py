
import json
import cv2
import numpy as np

global width
global height

FPS = 15
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
    
    return donation_zones,height,width

def parse_string(s):
  items = s.split('|')

  cls, t_id, _, x1_p, y1_p, x2_p, y2_p, conf = items

  x1, y1 = int(int(x1_p) * width / 10000), int(int(y1_p) * height / 10000)
  x2, y2 = int(int(x2_p) * width / 10000), int(int(y2_p) * height / 10000)

  cx = int((x1+x2)/2)
  cy = int((y1+y2)/2)

  return cls,int(t_id),x1,y1,cx,cy,float(conf) 

def get_coord(s):
  items = s.split('|')

  cls, t_id, _, x1_p, y1_p, x2_p, y2_p, conf = items

  x1, y1 = int(int(x1_p) * width / 10000), int(int(y1_p) * height / 10000)
  x2, y2 = int(int(x2_p) * width / 10000), int(int(y2_p) * height / 10000)
  
  return (x1,y1),(x2,y2)


def update_counter(counted_items,arm_items):
    c = 0
    for key,item in arm_items.items():        
        if (cv2.pointPolygonTest(donation_zones[0], item[0],False)==-1 and
            (cv2.pointPolygonTest(donation_zones[0], item[1],False)==1 or
             cv2.pointPolygonTest(donation_zones[1], item[1],False)==1)):
            
            counted_items.add(key)
            
        else:
            counted_items.discard(key)


donation_zones,height,width = get_donation_zones(donation_zones_path)
blank_image = np.ones((height,width,3),np.uint8)

for zone in donation_zones:
    cv2.polylines(blank_image, [zone], True, (0,255,0),3)

# out = cv2.VideoWriter('out.avi',cv2.VideoWriter_fourcc('M','J','P','G'),FPS,(height,width))
video = cv2.VideoWriter('out.mp4',cv2.VideoWriter_fourcc(*'mp4v'), 15,(width,height))

# Opening JSON file
f = open(data_path)

# returns JSON object as
    # a dictionary
data = json.load(f)['messages']

c=0
arm_items = {}
counted_items = set()
for frame in data:
  frame_image = blank_image.copy()
  
  cv2.putText(frame_image, "Frame Counter: "+str(frame['id']), (50,50), cv2.FONT_HERSHEY_SIMPLEX,2,(255,255,255))  
  cv2.putText(frame_image, "Time Stamp: "+str(frame['ts']), (900,50), cv2.FONT_HERSHEY_SIMPLEX,2,(255,255,255))  
    
  # processing each frame
  for i in frame['objects']:
      
    obj = parse_string(i)
    s,e = get_coord(i)
    if obj[0]== 'Arm_Item':
        cv2.rectangle(frame_image,s,e,(255,255,0),2)
        if obj[1] in arm_items:
            arm_items[obj[1]] = [arm_items[obj[1]][0],(obj[4],obj[5])]

        else:
            arm_items[obj[1]] = [(obj[4],obj[5]),(obj[4],obj[5])]
    elif obj[0]=='Cart':
        cv2.rectangle(frame_image,s,e,(0,0,255),2)
        
    else:
        cv2.rectangle(frame_image,s,e,(0,234,255),2)
        
       
  update_counter(counted_items, arm_items)
  if c == len(counted_items)-1:
      c+=1
  cv2.putText(frame_image, "Item Counter: "+str(max(c,len(counted_items))), (50,100), cv2.FONT_HERSHEY_SIMPLEX,2,(255,255,255))  
  video.write(frame_image)
  # cv2.imshow("Result",frame_image)
  
  # cv2.waitKey(0)
  
              
  
  print(frame['id'],max(c,len(counted_items)))
  # import time
  # time.sleep(0.100)
video.release()
cv2.destroyAllWindows()
print("Total items:",len(counted_items))
    
