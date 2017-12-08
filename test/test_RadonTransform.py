import os
import numpy as np
import cv2
from tqdm import tqdm

import matplotlib.pyplot as plt
from skimage.io import imread
from skimage.transform import radon
from radon_transform import generateRadonLines, findCrossPoint, drawRectangle 

import time
import pickle

#root = 'C:/Users/chulh/문서/Git/avm_dataset/test/'
set_num = 1
root = 'C:/Users/chulh/문서/Git/avm_dataset/dataset/hyu_171121/ss/set{}/labeled/class_1'.format(set_num)
img_root = 'C:/Users/chulh/문서/Git/avm_dataset/dataset/hyu_171121/rectified/set{}'.format(set_num)
output_dir = 'C:/Users/chulh/Documents/hyu_171121/set{}/'.format(set_num)
if os.path.isdir(output_dir) == False:
    os.mkdir(output_dir)

f0 = 9
f1 = 10

ang_init = 90
ang_margin = 10
ang_center = ang_init 
img_rescale = 0.25

measurements = []
for i in tqdm(range(f0,f1)):        
    img_file = os.path.join(root, '{:08d}.jpg'.format(i))
    img = imread(img_file, as_grey=True)
    img_src = imread(os.path.join(img_root, '{:08d}.jpg'.format(i)))    

    #start_time = time.time()
    kernel = np.ones((5,5),np.uint8)
    img = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)    
#    plt.imshow(img)
#    plt.show()
    
#    img = cv2.erode(img,kernel,iterations = 1)
#    plt.imshow(img)
#    plt.show()
    
    img = cv2.resize(img, None, fx=img_rescale, fy=img_rescale)
    img[img>0] = 255
#    plt.imshow(img)
#    plt.show()

    img_size = (img.shape[1], img.shape[0])
    
    # rdaon transform
    theta = []    
    for ang in range(ang_center-ang_margin, ang_center+ang_margin+1):
        if ang >= 180:
            ang = ang - 180
        elif ang < 0:
            ang = ang + 180
        theta.append(ang)
        
    prj_t = radon(img, theta=theta)
    
    center = prj_t.shape[0] // 2
    offset, ang_idx = np.unravel_index(prj_t.argmax(), prj_t.shape) # ang_ps1: radon image domain        
    ang_ps1 = theta[ang_idx]
        
    # line generation for principle angle 1
    lines_ps1 = generateRadonLines(prj_t, theta, ang_idx, 0.2, 10, center, img_size)
    
    # line generation for principle angle 2
    ang_ps2 = 0
    if ang_ps1 < 90:
        ang_ps2 = 90 + ang_ps1
    elif ang_ps1 > 90:
        ang_ps2 = ang_ps1 - 90
    elif ang_ps1 == 90:
        ang_ps2 = 0
        
    theta = [ang_ps2]
    prj_t = radon(img, theta=theta)    
    lines_ps2 = generateRadonLines(prj_t, theta, 0, 0.2, 10, center, (img.shape[1], img.shape[0]))
        
    img_debug = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)    
    pts = []    
    margin = 10
    for l1 in lines_ps1:    
        for l2 in lines_ps2:
            # cross point
            x, y = findCrossPoint((l1.get_a(), l1.get_b()), (l2.get_a(), l2.get_b()))
            if x >= 0 and x < img_size[0] and y >= 0 and y < img_size[1]:
                l1.set_cross_pt((x,y))
        l1.generate_pairs()        
        l1.classify_pairs(img, margin, True)             
        #img_debug = drawRectangle(img_debug, marginal_space)                        
    #print('execution time: {} ms'.format((time.time()-start_time)*1000))
       
    # ang center update
    ang_center = ang_ps1
    #print(ang_center)

    valid_per_ps = []
    valid_par_ps = []
    cross_pts = []
    for l in lines_ps1:
        if len(l.valid_per_ps) != 0:
            valid_per_ps.append(l.valid_per_ps)
        if len(l.valid_par_ps) != 0:
            valid_par_ps.append(l.valid_par_ps)
        if len(l.pts) != 0:
            cross_pts.append(l.pts)

    # draw
    img_debug = img_src
    for l in lines_ps1:
#        for ps in l.valid_per_ps:
#            img_debug = drawRectangle(img_debug, ps, 3, 1./img_rescale )
        for ps in l.valid_par_ps:
            img_debug = drawRectangle(img_debug, ps, 3, 1./img_rescale )
        for pt in l.pts:
            img_debug = cv2.circle(img_debug, (np.int(pt[0]/img_rescale), np.int(pt[1]/img_rescale)),3, (0,255,255), -1)
        
    measurements = {'per_ps': valid_per_ps, 'par_ps': valid_par_ps, 'cross_pts': cross_pts}
    
    plt.imshow(img_debug)    
    plt.show()
    #print(ang_center)
#    save_file = os.path.join(output_dir, '{:08d}.png'.format(i))
#    cv2.imwrite(save_file, img_debug)

pickle.dump(measurements, open(os.path.join(output_dir,'measurement.p'), 'wb'))



'''
plt.plot(prj_ps1)
plt.show()


iteration = 10
sum_time = 0
for i in range(iteration):
    start_time  = time.time()
    prj_t = radon(img)
    sum_time += time.time() - start_time
avg_time = sum_time / iteration
print("avg time [radon]: {} ms".format(avg_time * 1000))
'''

'''
iteration = 1
sum_time = 0
for i in range(iteration):
    start_time  = time.time()
    indexes = peakutils.indexes(prj_ps1.reshape(prj_ps1.shape[0],), thres=0.02/max(prj_ps1), min_dist=20) # 3.3ms
    sum_time += time.time() - start_time
avg_time = sum_time / iteration
print("avg time [peak detection]: {} ms".format(avg_time * 1000))
'''


