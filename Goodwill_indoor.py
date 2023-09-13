
import json
import cv2
import numpy as np

global width
global height

FLICKERING_THRESH = 25
IMAGINARY_ROI = 50

#Output video type, 1 for drawing 2 for original video
output_video = 2

FPS = 15
donation_zones_path = 'ADC-RIVER.OAKS-MACO2.jpg.json'

#first
# data_path = 'h264__2023-09-03_15-18-01-ADC-RIVER.OAKS-MACO2_09042023.json'
# video_path = 'h264__2023-09-03_15-18-01-ADC-RIVER.OAKS-MACO2_09042023.mp4'

# biggest video
data_path = 'JSONS/h264_2023-07-27_11-57-16-ADC-RIVER.OAKS-MACO2_09042023.json'
video_path = 'JSONS/h264_2023-07-27_11-57-16-ADC-RIVER.OAKS-MACO2_09042023.mp4'


show_video = True

counted_items_log = set()


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

  cls, t_id, _, x1_p, y1_p, x2_p, y2_p, _ = items

  x1, y1 = int(int(x1_p) * width / 10000), int(int(y1_p) * height / 10000)
  x2, y2 = int(int(x2_p) * width / 10000), int(int(y2_p) * height / 10000)
  
  return cls,t_id,(x1,y1),(x2,y2)


def update_counter(counted_items,arm_items,boxes):
    c = 0
    for key,item in arm_items.items():
        cond1 = True
        cond2 = False
        
        show=True

        for b in boxes:
            #start point is outside of any box
            cond1 = cond1 and not point_inside_rectangle(item[0],[b[0],b[1]])

            #end point is inside somebox
            cond2 = cond2 or (point_inside_rectangle(item[1],[b[0],b[1]]))
            if cond2 and show:
                show=False
                counted_items_log.add(f'{key} in {b[2]}')

                # print(key,'in',b[2])


        cond3 = True
        cond4 = False
        
        
        for d in donation_zones:
            cond3 = cond3 and (cv2.pointPolygonTest(d, item[0],True)<-IMAGINARY_ROI)
            cond4 = cond4 or (cv2.pointPolygonTest(d, item[1],False)==1)

            
        cond = cond1 and cond2 and cond3 and cond4

        if cond: 
            if item[2]>=FLICKERING_THRESH:
                counted_items.add(key)
            elif cond2==False:
                counted_items.discard(key)


donation_zones,height,width = get_donation_zones(donation_zones_path)

cap = cv2.VideoCapture(video_path)



blank_image = np.zeros((height,width,3),np.uint8)
# res, blank_image = cap.read()

def boxes_in_roi(objects):
    boxes = []
    for i in objects:
        cls,t_id,(x1,y1),(x2,y2) = get_coord(i)
        if cls in ['H','Duro','Tote']:
            cx = int((x1+x2)/2)
            cy = int((y1+y2)/2)

            for d in donation_zones:
                if cv2.pointPolygonTest(d, (cx,cy),False)==1:
                    boxes.append([(x1,y1),(x2,y2),t_id])

    return boxes

            


def point_inside_rectangle(point,rect):
    x,y = point
    (x1,y1),(x2,y2) = rect
    return x1<=x<=x2 and y1<=y<=y2





def draw_zones(image,donation_zones):
    for zone in donation_zones:
        cv2.polylines(image, [zone], True, (255, 0, 0), 2)
        new_coords_donation = (zone[0][0]-5,zone[0][1]-5)
        cv2.putText(image, "DonationZone", new_coords_donation, cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)


output_video = "".join(video_path.split('.')[:-1]).split('/')[-1]+'_out.mp4'
video = cv2.VideoWriter(output_video,cv2.VideoWriter_fourcc(*'mp4v'), FPS,(width,height))

# Opening JSON file
f = open(data_path)

# returns JSON object as
    # a dictionary
data = json.load(f)['messages']

c=0
counted_items = set()
arm_items = {}
for frame in data:
  if output_video ==1:
      frame_image = blank_image.copy()
  else:
      cap.set(cv2.CAP_PROP_POS_FRAMES, frame['id'])
      res, frame_image = cap.read()
      
  frame_image = cv2.resize(frame_image, (1920,1440))
  
  draw_zones(frame_image, donation_zones)

  if frame['id']==2000:
    print('here')
    break

  
  cv2.putText(frame_image, f"Frame number: {frame['id']}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)  
  cv2.putText(frame_image, "Time Stamp: "+str(frame['ts']), (1250,25), cv2.FONT_HERSHEY_SIMPLEX,1, (255, 255, 0), 2)

  boxes = boxes_in_roi(frame['objects'])  
  # boxes = [s,e]  
  # processing each frame
  for i in frame['objects']:
      
    obj = parse_string(i)
    # if obj[1]==761:
    #     print()
    _,_,s,e = get_coord(i)

    if obj[0]== 'Arm_Item':
        
        cv2.rectangle(frame_image,s,e,(0, 0, 255),2)
        s = (s[0],s[1]-5)
        # e = (e[0],e[1]-5)
        
        cv2.putText(frame_image, f"{obj[0]}#{obj[1]}", s, cv2.FONT_HERSHEY_SIMPLEX, 2,(0, 0, 255), 2)

        if obj[1] in arm_items:
            cnt = arm_items[obj[1]][2]+1 
            arm_items[obj[1]] = [arm_items[obj[1]][0],(obj[4],obj[5]),cnt]

        else:
            arm_items[obj[1]] = [(obj[4],obj[5]),(obj[4],obj[5]),1]
    elif obj[0]=='Cart':
        cv2.rectangle(frame_image,s,e,(255, 255, 255),2)
        s = (s[0],s[1]-5)
        # e = (e[0],e[1]-5)
        
        cv2.putText(frame_image, f"Human#{obj[1]}", s, cv2.FONT_HERSHEY_SIMPLEX, 1,(255, 255, 255), 2)
        
    else:
        cv2.rectangle(frame_image,s,e,(0, 255, 0),2)
        s = (s[0],s[1]-5)
        # e = (e[0],e[1]-5)
        
        cv2.putText(frame_image, f"{obj[0]}#{obj[1]}", s, cv2.FONT_HERSHEY_SIMPLEX, 1,(0, 255, 0), 2)
        
  update_counter(counted_items, arm_items,boxes)
  if c == len(counted_items)-1:
      c+=1
  cv2.putText(frame_image, "Item Counter: "+str(max(c,len(counted_items))), (50, 100), cv2.FONT_HERSHEY_SIMPLEX,1, (255, 255, 0), 2)  
  video.write(frame_image)
  if show_video:
      
      res = cv2.resize(frame_image, (0, 0), fx = 0.6, fy = 0.6)
      cv2.imshow("Result",res)
      
      
      cv2.waitKey(1)
  
              
  
  print(frame['id'],max(c,len(counted_items)))
  # import time
  # time.sleep(0.100)
  

video.release()
cv2.destroyAllWindows()
print(counted_items_log)
print(counted_items)
print("Total items:",len(counted_items))
    