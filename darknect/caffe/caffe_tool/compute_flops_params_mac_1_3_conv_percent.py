 #-*- coding:utf-8 -*-
import sys
# add your caffe/python path
sys.path.insert(0, "/home/wanyouwen/ewenwan/software/caffe-ssd/python")
# sys.path.insert(0, "/home/wanyouwen/ewenwan/software/quantization/caffe-ris-inq/python")
import caffe
import sys
caffe.set_mode_cpu()
import numpy as np
from numpy import prod, sum
from pprint import pprint

#all_flops = 0.0
all_MAC = 0.0

def print_net_parameters_flops (deploy_file):
    print ("Net: " + deploy_file)
    net = caffe.Net(deploy_file, caffe.TEST)
    flops = 0.0
    mac = 0.0
    num_1_1 = 0.0
    num_3_3 = 0.0
    # 卷积，逐通道卷积，全连接
    typenames = ['Convolution', 'DepthwiseConvolution', 'InnerProduct']
    print ("Layer-wise parameters: ")
    # 字符串长度 20
    print ('layer name'.ljust(20), 'Filter Shape'.ljust(20), \
            'Output Size'.ljust(20), 'Layer Type'.ljust(20), 'Flops'.ljust(20), 'MAC'.ljust(20))
    h_in = 224
    w_in = 224
    for layer_name, blob in net.blobs.items():
        if layer_name not in net.layer_dict:
            continue
        # 计算相应层
        if net.layer_dict[layer_name].type in typenames:
            cur_flops = 0.0
            cur_mac = 0.0
            #cur_num_1_1 = 0.0
            #cur_num_3_3 = 0.0
            '''
            # ['Convolution', 'DepthwiseConvolution']
            if net.layer_dict[layer_name].type in typenames[:2]:
                cur_flops = (np.product(net.params[layer_name][0].data.shape) * \
                        blob.data.shape[-1] * blob.data.shape[-2])
                # 特征图H*W * Weight_h * Weight_w
            # InnerProduct  c_in*c_out*1*1
            else:
                cur_flops = np.product(net.params[layer_name][0].data.shape)
                # 特征图H*W * 1*1
            '''
            h_out = blob.data.shape[2]
            w_out = blob.data.shape[3] 
            
            #'''
            # 卷积核维度 output_channel * input_channel * kernel_height * kernel_width
            # ['Convolution']
            if net.layer_dict[layer_name].type == typenames[0]:
                # 计算量 乘加次数 macc  = h_out*w_ou*c_in*c_out* k_h * k_w
                # 如果是 flops  近似为 2倍的 macc
                cur_flops = (np.product(net.params[layer_name][0].data.shape) * \
                             h_out*w_out)# 
                # 输出图面积 * 卷积核面积 * 输入通道数量 * 输出通道数量
                # 卷积核参数 net.params[layer_name][0].data
                # shape[0] shape[1] shape[2] shape[3]    输出数量Cout 输入数量Cin k_h  k_w             
                
                # mem acc cost 访存  h*w*c_in + h2*w2*c_out  + c_in*c_out* k_h*k_w
                cur_mac = (h_out*w_out*np.product(net.params[layer_name][0].data.shape) + \
                           h_out*w_out*net.params[layer_name][0].data.shape[0] + \
                           np.product(net.params[layer_name][0].data.shape))
                # 输入访问 + 输出内存大小 + 卷积核内存大小
                # 1. 输入(K × K × Cin) x (Hout x Wout x Cout)   一次访问输入数据大小(单个卷积核参数量) * 总共多少次(输出像素数量)
                # 2. 输出  output = Hout × Wout × Cout 计算一次，输出赋值一次
                # 3. 参数 weights = K × K × Cin × Cout + Cout 读取一次在缓存，Cout 个 维度为 K × K × Cin 的卷积核
                
                
                # 特征图H*W * Weight_h * Weight_w*c_in*c_out*2 / 1
                
                # 乘法和加法
            # ['DepthwiseConvolution'] 
            elif net.layer_dict[layer_name].type == typenames[1]:
                # 逐通道卷积  一个卷积核的厚度 从c_in 变为 1  相当于组卷积数量 为 输入c_in数量
                # 是普通卷积 的 macc / c_in
                cur_flops = (np.product(net.params[layer_name][0].data.shape) * \
                             h_out*w_out/net.params[layer_name][0].data.shape[1])
                # K × K × C_out × Hout × Wout
                
                # mac访存  h*w*c_in + h2*w2*c_out  + c_in*c_out*w_h*w_w/group
                cur_mac = (h_out*w_out*np.product(net.params[layer_name][0].data.shape)/net.params[layer_name][0].data.shape[1] + \
                           h_out*w_out*net.params[layer_name][0].data.shape[0] + \
                           np.product(net.params[layer_name][0].data.shape)/net.params[layer_name][0].data.shape[1])
                # 输入 输入(K × K × 1) x (Hout x Wout x Cout) 
                # 输出 h_out*w_out*C_out  
                # 权重 C_out * c_in *k_h * k_w / c_in    厚度从 c_in 变为1
                
                
            # InnerProduct  c_in*c_out*1*1
            else:
                cur_flops = np.product(net.params[layer_name][0].data.shape)
                # kernel特征图H*W = 1*1
                # flops = Weight_h * Weight_w * c_in*c_out*2
                
                # mac访存  h*w*c_in + 1*1*c_out  + c_in*c_out*w_h*w_w/group
                cur_mac = (h_in*w_in*net.params[layer_name][0].data.shape[1] + \
                           1*1*net.params[layer_name][0].data.shape[0] + \
                           np.product(net.params[layer_name][0].data.shape))
                
                
            #'''
            
            # 3*3卷积
            #if (net.params[layer_name][0].data.shape[2] == 3) and (net.params[layer_name][0].data.shape[2] == net.params[layer_name][0].data.shape[3]):
            if (net.params[layer_name][0].data.shape[2] == 3):
                num_3_3 += np.product(net.params[layer_name][0].data.shape);
            # 1*1卷积
            #if (net.params[layer_name][0].data.shape[2] == 1) and (net.params[layer_name][0].data.shape[2] == net.params[layer_name][0].data.shape):
            if (net.params[layer_name][0].data.shape[2] == 1):
                num_1_1 += np.product(net.params[layer_name][0].data.shape);
            
            h_in = h_out
            w_in = w_out
            # 打印当前层信息
            print(layer_name.ljust(20),
                    str(net.params[layer_name][0].data.shape).ljust(20), # filter 形状
                    str(blob.data.shape).ljust(20), # 输出特征图尺寸
                    net.layer_dict[layer_name].type.ljust(20), # 层类型
                    str(cur_flops).ljust(20),# flops运算量
                    str(cur_mac).ljust(20))  # mac 访存量
            '''
            # InnerProduct  c_in*c_out*1*1
            if len(blob.data.shape) == 2:
                # 特征图H*W * 1*1
                flops += prod(net.params[layer_name][0].data.shape)
            # ['Convolution', 'DepthwiseConvolution']  c_in * c_out* Weight_h * Weight_w
            else:
                # 特征图H*W * Weight_h * Weight_w
                flops += prod(net.params[layer_name][0].data.shape) * blob.data.shape[2] * blob.data.shape[3]
            '''
            flops += cur_flops;
            mac   += cur_mac;
    total_num_of_param = sum([prod(v[0].data.shape) for k, v in net.params.items()])
    total_num_of_param_1_1_3_3 = num_1_1 + num_3_3
    print ('layers num: ' + str(len(net.params.items())))
    print ("Total number of parameters: " + str(total_num_of_param))
    
    #print ("number of 1*1 conv's parameters: " + str(num_1_1) + "   percent: " + str(num_1_1/total_num_of_param_1_1_3_3))
    print ("number of 1*1 conv's parameters: " + str(num_1_1) + "   percent: " + str(num_1_1/total_num_of_param))
    
    #print ("number of 3*3 conv's parameters: " + str(num_3_3) + "   percent: " + str(num_3_3/total_num_of_param_1_1_3_3))
    print ("number of 3*3 conv's parameters: " + str(num_3_3) + "   percent: " + str(num_3_3/total_num_of_param))
    
    print ("Total number of flops: " + str(flops/1000000000.) + " GFLOPS")
    print ("Total number of MAC: " + str(mac/1000000000.) + " Gmacs")


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print ('Usage:')
        print ('python calc_params.py  deploy.prototxt')
        exit()
    deploy_file = sys.argv[1]
    print_net_parameters_flops(deploy_file)
