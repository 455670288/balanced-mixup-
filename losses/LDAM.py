import math
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

class LDAMLoss(nn.Module):

    def __init__(self, cls_num_list, max_m=0.5, weight=None, s=30):
        super(LDAMLoss, self).__init__()
        m_list = 1.0 / np.sqrt(np.sqrt(cls_num_list))
        m_list = m_list * (max_m / np.max(m_list))
        m_list = torch.cuda.FloatTensor(m_list)
        self.m_list = m_list
        assert s > 0
        self.s = s
        self.weight = weight

    def forward(self, x, target):
        index = torch.zeros_like(x, dtype=torch.uint8)
        index.scatter_(1, target.data.view(-1, 1), 1)

        index_float = index.type(torch.cuda.FloatTensor)
        batch_m = torch.matmul(self.m_list[None, :], index_float.transpose(0, 1))
        batch_m = batch_m.view((-1, 1))
        x_m = x - batch_m

        output = torch.where(index, x_m, x)
        return F.cross_entropy(self.s * output, target, weight=self.weight)
        torch.nn.CrossEntropyLoss

if __name__ =='__main__':
    from utils import fix_random
    fix_random(seed=0)

    num_of_class = 10
    cls_num_list =[5000, 2997,1796,1077,645,387,232,139,83,50]
    logits = torch.rand(5,num_of_class).cuda()
    labels =  torch.randint(0,num_of_class,size=(5,)).cuda()
    criterion = LDAMLoss(cls_num_list = cls_num_list,max_m=0.5,s=30,weight=None)
    print('criterion:',criterion)

    loss = criterion(logits,labels)
    print(loss)

    #print('loss:',loss)
   # print(loss.detach().numpy())
    #print(list(criterion.parameters())[0].shape)