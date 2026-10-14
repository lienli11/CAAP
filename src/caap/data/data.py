# -*- coding:utf-8 -*-
import os
from PIL import Image
import numpy as np

import torch
from torch.utils import data

class NormSingleROI(object):
    """
    Normalize the input image (exclude the black region) with 0 mean and 1 std.
    [c,h,w]
    """
    def __init__(self, outchannels=1):
        self.outchannels = outchannels

    def __call__(self, tensor):
        c,h,w = tensor.size()
   
        if c != 1:
            raise TypeError('only support graysclae image.')

        # print(tensor.size)

        tensor = tensor.view(c, h*w)
        idx = tensor > 0
        t = tensor[idx]

        # print(t)
        m = t.mean()
        s = t.std() 
        t = t.sub_(m).div_(s+1e-6)
        tensor[idx] = t
        
        tensor = tensor.view(c, h, w)

        if self.outchannels > 1:
            tensor = torch.repeat_interleave(tensor, repeats = self.outchannels, dim = 0)
    
        return tensor


class PalmPrint(data.Dataset):
    '''
    Load and process the ROI images::

    INPUT::
    txt: a text file containing pathes & labels of the input images \n
    transforms: None 
    train: True for a training set, and False for a testing set
    imside: the image size of the output image [imside x imside]
    outchannels: 1 for grayscale image, and 3 for RGB image

    OUTPUT::
    [batch, outchannels, imside, imside]
    '''
    
    def __init__(self, data_dir,norm, transforms=None, train=True, co3net=False,imside = 128, outchannels = 1,
                 split=None, indices=None):
        from torchvision import transforms as T

        self.train = train
        # split 决定读取 .pth 中的哪个划分, train 只决定数据增强; 二者解耦后才能从训练划分中切出验证集
        self.split = split if split is not None else ('train' if train else 'test')
        self.indices = indices
        self.norm = norm

        self.co3net = co3net

        self.imside = imside # 128, 224
        self.chs = outchannels # 1, 3

        self.data_dir = data_dir        

        self.transforms = transforms

        if transforms is None:

            if self.norm =="aug_0.5":
                if not train: 
                    self.transforms = T.Compose([        
                        # T.Resize(self.imside),                  
                        T.ToTensor(),   
                        T.Normalize([0.5],[0.5]),  
                        ]) 
                else:
                    self.transforms = T.Compose([ 
                        # T.Resize(self.imside),                  

                        T.ToTensor(),
                        T.Normalize([0.5],[0.5]),
                        ])
                    
            elif "aug_org" in self.norm:
                if not train: 
                    self.transforms = T.Compose([        
                        # T.Resize(self.imside),                  
                        T.ToTensor(),   
                        NormSingleROI(outchannels=self.chs)     
                        ]) 
                else:
                    self.transforms = T.Compose([ 
                        # T.Resize(self.imside),
                        T.RandomChoice(transforms=[
                            T.ColorJitter(brightness=0, contrast=0.05, saturation=0, hue=0),# 0.3 0.35
                            T.RandomResizedCrop(size=self.imside, scale=(0.8,1.0), ratio=(1.0, 1.0)),
                            T.RandomPerspective(distortion_scale=0.15, p=1),# (0.1, 0.2) (0.05, 0.05)
                            T.RandomChoice(transforms=[
                                T.RandomRotation(degrees=10,  expand=False, center=(0.5*self.imside, 0.0)),
                                T.RandomRotation(degrees=10, expand=False, center=(0.0, 0.5*self.imside)),
                            ]),
                        ]),     

                        T.ToTensor(),
                        NormSingleROI(outchannels=self.chs)                   

                        ])
            elif self.norm == "none":
                self.transforms = T.Compose([
                    T.ToTensor(),
                ])
            else:
                raise NameError
                
        self._read_data()

 
    def _read_data(self):
        """Load dataset file and normalize structure across formats.
        Supports both dict-with-subdict (images/labels) and list-of-pairs formats.
        """
        raw = torch.load(self.data_dir, weights_only=False)

        def to_img_lbl(split):
            # split could be dict {'images':..., 'labels':...} or list[(img,lbl),...]
            if isinstance(split, dict) and 'images' in split and 'labels' in split:
                return split['images'], split['labels']
            if isinstance(split, (list, tuple)) and len(split) > 0:
                # list of (image, label)
                imgs = [it[0] for it in split]
                lbls = [int(it[1]) if not isinstance(it[1], (int, torch.Tensor)) else int(it[1]) for it in split]
                return imgs, lbls
            raise TypeError('Unsupported dataset split format: {}'.format(type(split)))

        if self.split == 'train':
            images, labels = to_img_lbl(raw.get('train', raw.get('Train', {})))
        else:
            images, labels = to_img_lbl(raw.get('test', raw.get('Test', {})))

        if self.indices is not None:
            images = [images[i] for i in self.indices]
            labels = [labels[i] for i in self.indices]

        self.images = images
        self.labels = labels

    def __getitem__(self, index):
        label = self.labels[index]

       

        data = self.images[index] 
        data = self.transforms(data)    

        if self.co3net:
            idx2 = np.random.choice(np.arange(len(self.labels))[np.array(self.labels) == label])

            if self.train == True:
                while(idx2 == index):
                    idx2 = np.random.choice(np.arange(len(self.labels))[np.array(self.labels) == label])
            else:
                idx2 = index

            data2 = self.images[idx2] 
            data2 = self.transforms(data2)

            data = [data,data2]

        return data, int(label)#, img_path
    

    def __len__(self):
        return len(self.labels)


def split_train_val(labels, val_ratio, seed=0):
    """按身份分层地从训练划分中留出验证集, 每个身份至少保留 1 张训练图."""
    rng = np.random.RandomState(seed)
    labels = np.asarray(labels)
    train_idx, val_idx = [], []
    for c in np.unique(labels):
        idx = np.flatnonzero(labels == c)
        rng.shuffle(idx)
        n_val = int(round(len(idx) * val_ratio))
        n_val = min(max(n_val, 1 if len(idx) > 1 else 0), len(idx) - 1)
        val_idx.extend(idx[:n_val].tolist())
        train_idx.extend(idx[n_val:].tolist())
    return sorted(train_idx), sorted(val_idx)


def get_data(args):
    if not getattr(args, "data_path", None):
        raise ValueError("data_path must be provided explicitly; only load trusted legacy .pth datasets")
    args.data_dir = os.path.abspath(os.path.expanduser(args.data_path))
    if not os.path.isfile(args.data_dir):
        raise FileNotFoundError(f"data_path is not an existing file: {args.data_dir}")

    testset = PalmPrint(data_dir=args.data_dir, norm=args.norm, transforms=None, train=False, co3net=args.co3net)

    val_ratio = getattr(args, "val_ratio", 0.0)
    if val_ratio > 0:
        full_train = PalmPrint(data_dir=args.data_dir, norm=args.norm, transforms=None, train=True, co3net=args.co3net)
        train_idx, val_idx = split_train_val(full_train.labels, val_ratio, getattr(args, "split_seed", 0))
        trainset = PalmPrint(data_dir=args.data_dir, norm=args.norm, transforms=None, train=True,
                             co3net=args.co3net, split='train', indices=train_idx)
        valset = PalmPrint(data_dir=args.data_dir, norm=args.norm, transforms=None, train=False,
                           co3net=args.co3net, split='train', indices=val_idx)
    else:
        print("WARNING: val_ratio=0, validation falls back to the test split (legacy behaviour)")
        trainset = PalmPrint(data_dir=args.data_dir, norm=args.norm, transforms=None, train=True, co3net=args.co3net)
        valset = testset

    num_workers = getattr(args, "num_workers", 4)

    trainloader = torch.utils.data.DataLoader(
        trainset, batch_size=args.batch_size, shuffle=True, num_workers=num_workers)
    valloader = torch.utils.data.DataLoader(
        valset, batch_size=args.batch_size, shuffle=False, num_workers=num_workers)
    testloader = torch.utils.data.DataLoader(
        testset, batch_size=args.batch_size, shuffle=False, num_workers=num_workers)

    return trainloader, valloader, testloader
