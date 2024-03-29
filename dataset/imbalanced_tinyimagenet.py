import torch, torchvision
import torchvision.datasets as datasets
import torchvision.transforms as transforms
import numpy as np
from torch.utils.data import Dataset
from utils import split_train_valid


class SimpleDataset(Dataset):
    def __init__(self, x, y, transform=None):
        self.data = x
        self.targets = y
        self.transform = transform
    
    def __getitem__(self, index):
        img = self.data[index]
        if self.transform is not None:
            img = self.transform(img)
        target = self.targets[index]
        return img, target  # return sample pair
    
    def __len__(self):
        return len(self.data)


class ImbalanceTinyImageNet(Dataset):
    
    def __init__(self, x, y, cls_num=200, imb_type='exp', imb_factor=0.01, minority_label=None, transform=None,
                 rand_number=0):
        np.random.seed(rand_number)
        self.transform = transform
        self.minority_label = minority_label
        self.cls_num = cls_num
        img_num_list = self.get_img_num_per_cls(x, imb_type, imb_factor)
        self.data, self.targets = self.gen_imbalanced_data(x, y, img_num_list)
    
    def get_img_num_per_cls(self, x, imb_type, imb_factor):
        # img_max = 500
        img_max = len(x) / self.cls_num
        img_num_per_cls = []
        if imb_type == 'exp':
            for cls_idx in range(self.cls_num):
                num = img_max * (imb_factor ** (cls_idx / (self.cls_num - 1.0)))
                img_num_per_cls.append(int(num))
        elif imb_type == 'step':
            for cls_idx in range(self.cls_num // 2):
                img_num_per_cls.append(int(img_max))
            for cls_idx in range(self.cls_num // 2):
                img_num_per_cls.append(int(img_max * imb_factor))
        elif imb_type == 'minority':
            img_num_per_cls = np.array([int(img_max)] * self.cls_num)
            # set the minority group with imb_factor
            img_num_per_cls[self.minority_label] = int(img_max * imb_factor)
            img_num_per_cls = list(img_num_per_cls)
        
        else:
            img_num_per_cls = [int(img_max)] * self.cls_num
        return img_num_per_cls
    
    def gen_imbalanced_data(self, x, y, img_num_per_cls):
        new_data = []
        new_targets = []
        targets_np = np.array(y, dtype=np.int64)
        classes = np.unique(targets_np)
        self.num_per_cls_dict = dict()
        # temp = []
        for the_class, the_img_num in zip(classes, img_num_per_cls):
            self.num_per_cls_dict[the_class] = the_img_num
            idx = np.where(targets_np == the_class)[0]
            # temp.append(len(idx))
            np.random.shuffle(idx)
            selec_idx = idx[:the_img_num]
            new_data.append(x[selec_idx, ...])
            new_targets.extend([the_class, ] * the_img_num)
        # print(temp)
        new_data = torch.tensor(np.vstack(new_data))
        new_targets = torch.tensor(new_targets)
        return new_data, new_targets
    
    def get_cls_num_list(self):
        cls_num_list = []
        for i in range(self.cls_num):
            cls_num_list.append(self.num_per_cls_dict[i])
        return cls_num_list
    
    def __getitem__(self, index):
        img = self.data[index]
        if self.transform is not None:
            img = self.transform(img)
        target = self.targets[index]
        return img, target
    
    def __len__(self):
        return len(self.data)


if __name__ == "__main__":
    transform_train = transforms.Compose([
        transforms.RandomCrop(64),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize((0.4802, 0.4481, 0.3975), (0.2770, 0.2691, 0.2821)),
    ])
    
    data_dir = '/home/omnisky/loss_hly/Tiny_imagenet/tiny-imagenet-200'
    split_train_valid(data_dir=data_dir, n_sample=50)
    
    train_x = torch.load(data_dir + '/train_x.pt')
    train_label = torch.load(data_dir + '/train_label.pt')
    print(len(train_x))
    trainset = ImbalanceTinyImageNet(train_x, train_label, transform=transforms)
    cls_num_list = trainset.get_cls_num_list()
    print(cls_num_list)
