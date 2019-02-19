import numpy as np


def sigmoid(Z):
    return 1/(1+np.exp(-Z))


def sigmoid_backward(dA, Z):
    sig = sigmoid(Z)
    return dA * sig * (1 - sig)


def relu(Z):
    return Z * (Z > 0)


def relu_backward(dA, Z):
    return dA * (Z > 0)
