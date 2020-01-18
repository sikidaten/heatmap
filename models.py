import torch
import torch.nn as nn
from mobilenet import mobilenet_v2, MobileNetV2
from resnet import resnet152
import torch.nn.functional as F
import numpy  as np
import os


def vec2img(vec, size, sp):
    # ATTENNTION!!(C,H,W)
    c = vec.shape[-1]
    vec = vec.reshape(-1, sp, sp, c)
    vec = vec.permute(0, 3, 2, 1)
    vec = F.interpolate(vec, (size, size))
    return vec


class ImgPackModel(nn.Module):
    def __init__(self,param='REG'):
        assert param=='REG'
        super(ImgPackModel, self).__init__()
        self.biclsmodel = PatchModel(2)
        patchmodelsavedpath = 'patchmodel.pth'
        if os.path.exists(patchmodelsavedpath):
            self.biclsmodel.load_state_dict(torch.load(patchmodelsavedpath))
            print('load', patchmodelsavedpath)

        self.feature = MobileNetV2(9)
        #self.feature=resnet152(in_channel=9)
        self.classifier = nn.Sequential(
            nn.Dropout(0.2),
            nn.Linear(1000, 2),
        )
        self.locator=nn.Sequential(
            nn.Dropout(0.2),
            nn.Linear(1000,4),
            nn.Sigmoid()
        )

    def forward(self, img, splittedimg, bbox, mappedbox):
        #with torch.no_grad():
        #    splittedimg = self.biclsmodel(splittedimg)
        #    splittedimg = nn.Softmax(splittedimg)
        #splittedimg = vec2img(splittedimg, 128, 6)
        # x = torch.cat([mappedbox, splittedimg, img], dim=1)
        x = torch.cat([mappedbox, img], dim=1)
        # x=img
        x = self.feature(x)
        obj = self.classifier(x)
        coor=self.locator(x)
        return obj,coor


class PatchModel(nn.Module):
    def __init__(self, cls):
        super(PatchModel, self).__init__()
        self.cnn = mobilenet_v2(pretrained=False)
        self.fc1 = nn.Linear(1000, 256)
        self.fc2 = nn.Linear(256, 16)
        self.fc3 = nn.Linear(16, cls)

    def forward(self, x):
        # with torch.no_grad():
        s = x.shape
        x = x.reshape(-1, *s[-3:])
        x = self.cnn(x)
        x = F.relu(x)
        x = self.fc1(x)
        x = F.relu(x)
        x = self.fc2(x)
        x = F.relu(x)
        x = self.fc3(x)
        x = x.view(*s[:2], 2)
        return x
