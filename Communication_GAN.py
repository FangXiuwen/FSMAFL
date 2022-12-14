import os
from data_utils import generate_partial_femnist,pre_handle_femnist_mat,get_mnist_dataset,get_device_num,get_device_id
from models import CNN_3layer_fc_model,CNN_2layer_fc_model,CNN_3layer_fc_model_no_softmax,CNN_2layer_fc_model_no_softmax,DomainIdentifierNew
from collaborate_train import train_models_bal_femnist_collaborate,feature_domain_alignment,train_models_collaborate_gan
from model_utils import get_model_list,get_femnist_model_list,test_models_femnist
from matplotlib.pyplot import MultipleLocator #从pyplot导入MultipleLocator类，这个类用于设置刻度间隔
from models import DomainIdentifier
import matplotlib.pyplot as plt
from option import args_parser
import mindspore
from mindspore import save_checkpoint
from mindspore.communication.management import init
from mindspore import context

def transpose( matrix):
    """
    Matrix transpose
    """
    new_matrix = []
    for i in range(len(matrix[0])):
        matrix1 = []
        for j in range(len(matrix)):
            matrix1.append(matrix[j][i])
        new_matrix.append(matrix1)
    return new_matrix

if __name__ == '__main__':
    """
    Init context
    """
    args = args_parser()
    # device ='cuda' if args.gpu else 'cpu'
    mindspore.context.set_context(mode=mindspore.context.GRAPH_MODE, device_target=args.device_target)
    device = 'Ascend'
    context.set_context(mode=context.GRAPH_MODE,
                        device_target=args.device_target)
    device_num = get_device_num()
    if args.device_target == "Ascend":
        device_id = get_device_id()
        context.set_context(device_id=device_id)
        if device_num > 1:
            context.reset_auto_parallel_context()
            context.set_auto_parallel_context(device_num=device_num, parallel_mode='data_parallel',
                                              gradients_mean=True)
            init()

    """
    Init models
    """
    datasetindex = 0
    models = {"2_layer_CNN": CNN_2layer_fc_model,"3_layer_CNN": CNN_3layer_fc_model}
    models_no_softmax = {"2_layer_CNN": CNN_2layer_fc_model_no_softmax,"3_layer_CNN": CNN_3layer_fc_model_no_softmax}
    models_ini_list = [{"model_type": "2_layer_CNN", "params": {"n1": 128, "n2": 256, "dropout_rate": 0.2}},
                       {"model_type": "2_layer_CNN", "params": {"n1": 128, "n2": 384, "dropout_rate": 0.2}},
                       {"model_type": "2_layer_CNN", "params": {"n1": 128, 'n2': 512, "dropout_rate": 0.2}},
                       {"model_type": "2_layer_CNN", "params": {"n1": 256, "n2": 256, "dropout_rate": 0.3}},
                       {"model_type": "2_layer_CNN", "params": {"n1": 256, "n2": 512, "dropout_rate": 0.4}}]

    accuracy = []
    models_list = []
    eachround_accuracy = []
    root = "./Model"
    name = ["Femnist_model_0.ckpt", "Femnist_model_1.ckpt", "Femnist_model_2.ckpt",
            "Femnist_model_3.ckpt", "Femnist_model_4.ckpt"]
    models_list = get_model_list(root=root, name=name, models_ini_list=models_ini_list, models=models)

    """
    Generate femnist dataset
    """
    X_train, y_train, writer_ids_train, X_test, y_test, writer_ids_train, writer_ids_test = pre_handle_femnist_mat()
    y_train += len(args.public_classes)
    y_test += len(args.public_classes)
    femnist_X_test, femnist_y_test = generate_partial_femnist(X=X_test, y=y_test, class_in_use=args.private_classes,
                                                              verbose=False)

    """
    Test the models on femnist
    """
    figureurl = 'Figures/mnist/collaborate_gan/'
    eachround_accuracy = test_models_femnist(device=device, models_list=models_list, test_x=femnist_X_test,
                                             test_y=femnist_y_test, savelurl=figureurl)
    accuracy.append(eachround_accuracy)

    """
    Define GanModel0
    """
    net = DomainIdentifier()
    save_checkpoint(net, 'GanModel0.ckpt')

    """
    federated communication
    """
    for item in range(args.Communicationepoch):
        print('This is {} time communication'.format(item))
        '''
        Generate MNIST
        '''
        mnist_data_train, mnist_data_validation, mnist_data_test = get_mnist_dataset()

        '''
        For Latent Embedding Adaptation
        '''
        root = "./Model"
        name = ["Femnist_model_0.ckpt", "Femnist_model_1.ckpt", "Femnist_model_2.ckpt",
                "Femnist_model_3.ckpt", "Femnist_model_4.ckpt"]
        models_list = get_model_list(root=root, name=name, models_ini_list=models_ini_list, models=models)
        feature_domain_alignment(device=device, train=mnist_data_train,
                                 models_list=models_list, modelurl=root,
                                 domain_identifier_epochs=args.Communication_domain_identifier_epochs,
                                 gan_local_epochs=args.Communication_gan_local_epochs)
        '''
        model agnostic federated learning
        '''
        root = "./Model/collaborate_gan"
        name = ["LocalModel0.ckpt", "LocalModel1.ckpt", "LocalModel2.ckpt",
                "LocalModel3.ckpt", "LocalModel4.ckpt"]
        models_list= get_model_list(root=root,name=name,models_ini_list=models_ini_list, models=models_no_softmax)
        train_models_collaborate_gan(device=device, models_list=models_list,
                                       train=mnist_data_train,  user_number=args.user_number,
                                       collaborative_epoch=args.collaborative_epoch,output_classes=args.output_classes)

        root = "./Model/final_model"
        name = ["LocalModel0.ckpt", "LocalModel1.ckpt", "LocalModel2.ckpt",
                "LocalModel3.ckpt", "LocalModel4.ckpt"]
        models_list= get_model_list(root=root,name=name,models_ini_list=models_ini_list, models=models_no_softmax)
        train_models_bal_femnist_collaborate(device=device, models_list=models_list,modelurl=root)

        """
        Get the updated models
        """
        models_list= get_model_list(root=root,name=name,models_ini_list=models_ini_list, models=models_no_softmax)
        """
        Create test dataset
        """
        X_train, y_train, writer_ids_train, X_test, y_test, writer_ids_train, writer_ids_test = pre_handle_femnist_mat()
        y_train += len(args.public_classes)
        y_test += len(args.public_classes)
        femnist_X_test, femnist_y_test = generate_partial_femnist(X=X_test, y=y_test, class_in_use=args.private_classes, verbose=False)

        figureurl = 'Figures/mnist/collaborate_gan/'
        eachround_accuracy = test_models_femnist(device=device, models_list=models_list, test_x=femnist_X_test,
                                                 test_y=femnist_y_test, savelurl=figureurl)
        accuracy.append(eachround_accuracy)
    print(accuracy)
    accuracy = transpose(accuracy)
    for i, val in enumerate(accuracy):
        print(val)
        plt.plot(range(len(val)), val, label='model :' + str(i))
    plt.legend(loc='best')
    plt.title('communication_round_with_accuracy_on_femnist')
    plt.xlabel('Communication round')
    plt.ylabel('Accuracy on FEMNIST')
    x_major_locator = MultipleLocator(1)
    ax = plt.gca()
    ax.xaxis.set_major_locator(x_major_locator)
    plt.xlim(0, args.Communicationepoch)
    figureurl = 'Figures/mnist/collaborate_gan/'
    plt.savefig(figureurl + 'communication_round_with_accuracy_on_femnist.png')
    plt.show()
    print('End')

