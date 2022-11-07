import mindspore.nn as nn

class CNN_2layer_fc_model(nn.Cell):
    def __init__(self,params):
        super(CNN_2layer_fc_model, self).__init__()
        n_one = params["n1"]
        n_two = params["n2"]
        dropout_rate = params["dropout_rate"]
        self.CNN1 = nn.SequentialCell([nn.Conv2d(in_channels=1, kernel_size=3, out_channels=n_one, padding=1, pad_mode='pad', has_bias=True),
                                       nn.BatchNorm2d(n_one, momentum=0.1),
                                       nn.ReLU(),
                                       # nn.Dropout(keep_prob=dropout_rate),
                                       nn.AvgPool2d(kernel_size=2, stride=1)
                                       ])
        self.CNN2 = nn.SequentialCell([nn.Conv2d(in_channels=n_one, stride=2, kernel_size=3, out_channels=n_two, pad_mode="valid", has_bias=True),
                                       nn.BatchNorm2d(n_two, momentum=0.1),
                                       nn.ReLU()
                                       # nn.Dropout(keep_prob=dropout_rate)
                                       ])
        self.FC1 = nn.Dense(169*n_two,16)

    def construct(self, x,GAN=False):
        x = self.CNN1(x)
        x = self.CNN2(x)
        x = x.view((x.shape[0], -1))
        if GAN:
            return x
        else: 
            x = self.FC1(x)
            return nn.LogSoftmax()(x)

class CNN_2layer_fc_model_no_softmax(nn.Cell):
    def __init__(self,params):
        super(CNN_2layer_fc_model_no_softmax, self).__init__()
        n_one = params["n1"]
        n_two = params["n2"]
        dropout_rate = params["dropout_rate"]
        self.CNN1 = nn.SequentialCell([nn.Conv2d(in_channels=1, kernel_size=3, out_channels=n_one, padding=1, pad_mode='pad', has_bias=True),
                                       nn.BatchNorm2d(n_one, momentum=0.1),
                                       nn.ReLU(),
                                       # nn.Dropout(keep_prob=dropout_rate),
                                       nn.AvgPool2d(kernel_size=2, stride=1)
                                       ])
        self.CNN2 = nn.SequentialCell([nn.Conv2d(in_channels=n_one, stride=2, kernel_size=3, out_channels=n_two, pad_mode="valid", has_bias=True),
                                       nn.BatchNorm2d(n_two, momentum=0.1),
                                       nn.ReLU()
                                       # nn.Dropout(keep_prob=dropout_rate)
                                       ])
        self.FC1 = nn.Dense(169*n_two,16)
    def construct(self, x):
        x = self.CNN1(x)
        x = self.CNN2(x)
        x = x.view(x.shape[0], -1)
        x = self.FC1(x)
        return x

class DomainIdentifier(nn.Cell):
    def __init__(self):
        super(DomainIdentifier, self).__init__()
        self.resize_layer_zero = nn.SequentialCell([nn.Dense(43264,128),nn.BatchNorm1d(128),nn.ReLU()])
        self.resize_layer_one = nn.SequentialCell([nn.Dense(64896,128),nn.BatchNorm1d(128),nn.ReLU()])
        self.resize_layer_two = nn.SequentialCell([nn.Dense(86528,128),nn.BatchNorm1d(128),nn.ReLU()])
        self.resize_layer_three = nn.SequentialCell([nn.Dense(43264,128),nn.BatchNorm1d(128),nn.ReLU()])
        self.resize_layer_four = nn.SequentialCell([nn.Dense(86528,128),nn.BatchNorm1d(128),nn.ReLU()])
        self.resize_layer_five = nn.SequentialCell([nn.Dense(2304,128),nn.BatchNorm1d(128),nn.ReLU()])
        self.resize_layer_six = nn.SequentialCell([nn.Dense(1728,128),nn.BatchNorm1d(128),nn.ReLU()])
        self.resize_layer_seven = nn.SequentialCell([nn.Dense(2304,128),nn.BatchNorm1d(128),nn.ReLU()])
        self.resize_layer_eight = nn.SequentialCell([nn.Dense(1152,128),nn.BatchNorm1d(128),nn.ReLU()])
        self.resize_layer_nine = nn.SequentialCell([nn.Dense(1728,128),nn.BatchNorm1d(128),nn.ReLU()])
        self.resize_dict = {0:self.resize_layer_zero,1:self.resize_layer_one,2:self.resize_layer_two,3:self.resize_layer_three,
                            4:self.resize_layer_four,5:self.resize_layer_five,6:self.resize_layer_six,7:self.resize_layer_seven,
                            8:self.resize_layer_eight,9:self.resize_layer_nine}
        self.resize_list = [self.resize_layer_zero,self.resize_layer_one,self.resize_layer_two,self.resize_layer_three,
                            self.resize_layer_four,self.resize_layer_five,self.resize_layer_six,self.resize_layer_seven,
                            self.resize_layer_eight,self.resize_layer_nine]
        self.fc1 = nn.Dense(128,64)
        self.fc2 = nn.Dense(64,11)
    def construct(self,x,index):
        x = x.view(x.shape[0],-1)
        x = self.resize_list[index](x)
        x = nn.LeakyReLU()(self.fc1(x))
        x = nn.LeakyReLU()(self.fc2(x))
        return x
