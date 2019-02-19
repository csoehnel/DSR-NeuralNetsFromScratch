import numpy as np
import warnings

from .activations import sigmoid, sigmoid_backward
from .activations import relu, relu_backward

from .utils import get_cost_value

import pdb

class Model():

    def __init__(self, architecture):
        if len(architecture) < 1 and architecture[0]['type'] != 'input':
            raise Exception("Model architecture must be deeper than one layer and first layer type must be input")
        self.architecture = architecture
        # let's initialize layers at first...
        self.init_layers()
        # Workshop #7: implement momentum
        self.reset_momentum()
        # Workshop #8: implement rmsprop
        self.reset_rmsprop()
        # Workshop #10: dropout
        self.train()

    def train(self):
        # Workshop #10: dropout
        self.training_mode = True

    def eval(self):
        # Workshop #10: dropout
        self.training_mode = False

    def init_layers(self, seed=42):
        # random seed initiation
        np.random.seed(seed)
        # number of layers in our neural network, input layer doesn't count
        number_of_layers = len(self.architecture) - 1
        # parameters storage initiation
        self.params_values = {}

        # iteration over network layers
        for layer_idx in range(1, len(self.architecture)):
            # extracting the number of units in layers
            # input size from the previous layer:
            layer_input_size = self.architecture[layer_idx-1]["dimension"]
            # output size from the current layer:
            layer_output_size = self.architecture[layer_idx]["dimension"]

            # initiating the values of the W matrix
            # randomness is important here: otherwise all neurons will learn in the same way
            # try to tweak the random factor, make it a parameter or google for some other heuristics
            # as described here: https://medium.com/usf-msds/deep-learning-best-practices-1-weight-initialization-14e5c0295b94
            self.params_values['W' + str(layer_idx)] = \
                np.random.randn(layer_output_size, layer_input_size) * 0.1
            # initiating the values of b
            # this can be either all zero or random
            self.params_values['b' + str(layer_idx)] = \
                np.zeros((layer_output_size, 1))

    def model_info(self):
        for layer_idx in range(1, len(self.architecture)):
            layer = self.architecture[layer_idx]
            print("Layer {}: {} with dimension {}".format(layer_idx, layer["type"], layer["dimension"]))
            print("W shape: {}".format(self.params_values['W' + str(layer_idx)].shape))
            print("b shape: {}".format(self.params_values['b' + str(layer_idx)].shape))

    def forward(self, X):
        # creating a temporary memory to store the information needed for a backward step
        self.memory = {}
        # X vector is the activation for layer 0
        A_curr = X

        # iteration over network layers
        for layer_idx in range(1, len(self.architecture)):
            # transfer the activation from the previous iteration
            A_prev = A_curr

            # extraction of W for the current layer
            W_curr = self.params_values["W" + str(layer_idx)]
            # extraction of b for the current layer
            b_curr = self.params_values["b" + str(layer_idx)]

            # Workshop #1: implement forward-pass
            # just apply the formulas with the parameters W_curr and b_curr
            # you need to store a variable called Z_curr for posterity (will be clearer later)
            # and A_curr which is needed in the next iteration of the loop and as a return value
            Z_curr = np.dot(W_curr, A_prev) + b_curr
            if self.architecture[layer_idx]["type"] == "sigmoid":
                activation = sigmoid(Z_curr)
            else:
                activation = relu(Z_curr)
            A_curr = activation

            # Workshop #10: dropout
            if self.training_mode and "dropout" in self.architecture[layer_idx]:
                keep_prob = 1 - self.architecture[layer_idx]["dropout"]
                u1 = np.random.binomial(1, p = keep_prob, size = A_curr.shape) / keep_prob
                A_curr *= u1
                self.memory["dropout" + str(layer_idx)] = u1

            # saving calculated values in the memory
            self.memory["A" + str(layer_idx-1)] = A_prev
            self.memory["Z" + str(layer_idx)] = Z_curr

        # saving current prediction vector as Y_hat
        # for future back_propagation but also it's
        # the function return value when used for inference
        self.Y_hat = A_curr

        # return Y_hat
        return self.Y_hat

    def back_propagation(self, Y):
        self.grads_values = {}

        # Y_hat has the shape of (ouput_dim, no_examples)
        # because we do binary classification only Y might have the
        # shape of (no_sample), so a reshape of Y is needed here
        Y = Y.reshape(self.Y_hat.shape)

        # number of examples
        m = Y.shape[1]

        # initiation of gradient descent algorithm
        # hardcoded derivative of log_loss wrt Y_hat
        # which is the input of backpropagation algorithm

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dA_prev = - (np.divide(Y, self.Y_hat) - np.divide(1 - Y, 1 - self.Y_hat))
            dA_prev[self.Y_hat == 0] = 1 #dA_prev[(Y == 0 and self.Y_hat == 0)] = 1
            dA_prev[self.Y_hat == 1] = -1 #dA_prev[(Y == 1 and self.Y_hat == 1)] = -1

        # back-propagation algorithm requires that we iterate over layer backwards...
        for layer_idx in range(len(self.architecture)-1, 0, -1):
            dA_curr = dA_prev

            # Workshop #10: dropout
            if self.training_mode and "dropout" in self.architecture[layer_idx]:
                u1 = self.memory["dropout" + str(layer_idx)]
                dA_curr *= u1

            # let's grab value of activations and Z of the previous layer
            # that we stored while the forward step...
            A_prev = self.memory["A" + str(layer_idx-1)]
            Z_curr = self.memory["Z" + str(layer_idx)]

            W_curr = self.params_values["W" + str(layer_idx)]
            b_curr = self.params_values["b" + str(layer_idx)]

            # number of examples
            m = A_prev.shape[1]

            # Workshop #3: implement back-propagation
            # some suggestions:
            # dA_curr is already computed correctly
            # dZ_curr depends on the activation function aka layer type
            # dW_curr is just like the formula
            # db_curr is just like the formula, but pay extra care on
            # the dimensions of numpy array
            # call dA[l-1] as dA_prev, the assignment at the beginning of the loop
            # will do the rest
            if self.architecture[layer_idx]["type"] == "sigmoid":
                activation_backward = sigmoid_backward(dA_curr, Z_curr)
            else:
                activation_backward = relu_backward(dA_curr, Z_curr)
            dZ_curr = activation_backward # dA_curr already multiplied in function
            dW_curr = np.dot(dZ_curr, A_prev.T) / m
            db_curr = np.sum(dZ_curr, axis = 1, keepdims = True) / m
            dA_prev = np.dot(W_curr.T, dZ_curr)

            self.grads_values["dW" + str(layer_idx)] = dW_curr
            self.grads_values["db" + str(layer_idx)] = db_curr

    def optimization_step(self, learning_rate):
        # Workshop #2: implement vanilla gradient descent step
        # Hint: you need grads_values and params_values...
        for layer_idx in range(1, len(self.architecture)):
            self.params_values["W" + str(layer_idx)] -= learning_rate * self.grads_values["dW" + str(layer_idx)]
            self.params_values["b" + str(layer_idx)] -= learning_rate * self.grads_values["db" + str(layer_idx)]

    def reset_momentum(self):
        # Workshop #7: implement momentum
        self.momentum = {}
        for layer_idx in range(1, len(self.architecture)):
            layer_input_size = self.architecture[layer_idx-1]["dimension"]
            layer_output_size = self.architecture[layer_idx]["dimension"]
            # momentum
            self.momentum['dW' + str(layer_idx)] = np.zeros((layer_output_size, layer_input_size))
            self.momentum['db' + str(layer_idx)] = np.zeros((layer_output_size, 1))

    def reset_rmsprop(self):
        # Workshop #8: implement rmsprop
        self.rmsprop = {}
        for layer_idx in range(1, len(self.architecture)):
            layer_input_size = self.architecture[layer_idx - 1]["dimension"]
            layer_output_size = self.architecture[layer_idx]["dimension"]
            # rmsprop
            self.rmsprop['dW' + str(layer_idx)] = np.zeros((layer_output_size, layer_input_size))
            self.rmsprop['db' + str(layer_idx)] = np.zeros((layer_output_size, 1))

    def optimization_step_momentum(self, learning_rate, running_counter, decay_rate=0.9):
        # Workshop #7: implement momentum
        for layer_idx in range(1, len(self.architecture)):
            self.momentum["dW" + str(layer_idx)] = (decay_rate * self.momentum["dW" + str(layer_idx)]) + \
                                                   ((1 - decay_rate) * self.grads_values["dW" + str(layer_idx)])
            self.momentum["db" + str(layer_idx)] = (decay_rate * self.momentum["db" + str(layer_idx)]) + \
                                                   ((1 - decay_rate) * self.grads_values["db" + str(layer_idx)])
            self.params_values["W" + str(layer_idx)] -= learning_rate * (self.momentum["dW" + str(layer_idx)] /
                                                                         (1 - np.power(decay_rate, running_counter))) # with bias-correction
            self.params_values["b" + str(layer_idx)] -= learning_rate * (self.momentum["db" + str(layer_idx)] /
                                                                         (1 - np.power(decay_rate, running_counter))) # with bias-correction
    def optimization_step_rmsprop(self, learning_rate, decay_rate=0.1):
        # Workshop #8: implement rmsprop
        beta = 1 - decay_rate

        for layer_idx in range(1, len(self.architecture)):
            self.rmsprop["dW" + str(layer_idx)] = (beta * self.rmsprop["dW" + str(layer_idx)]) + ((1 - beta) * np.multiply(self.grads_values["dW" + str(layer_idx)], self.grads_values["dW" + str(layer_idx)]))
            self.rmsprop["db" + str(layer_idx)] = (beta * self.rmsprop["db" + str(layer_idx)]) + ((1 - beta) * np.multiply(self.grads_values["db" + str(layer_idx)], self.grads_values["db" + str(layer_idx)]))
            self.params_values["W" + str(layer_idx)] -= learning_rate * np.divide(self.grads_values["dW" + str(layer_idx)],
                                                                                  np.sqrt(self.rmsprop["dW" + str(layer_idx)]
                                                                                          + np.finfo(np.float32).eps))
            self.params_values["b" + str(layer_idx)] -= learning_rate * np.divide(self.grads_values["db" + str(layer_idx)],
                                                                                  np.sqrt(self.rmsprop["db" + str(layer_idx)]
                                                                                          + np.finfo(np.float32).eps))

    def fit(self, X, Y, no_epochs, learning_rate, mini_batch_size=32, print_every=100, momentum_decay_rate = 0.0, rmsprop = False):
        # WORKSHOP #6
        running_counter = 0
        running_cost = 0
        num_samples = X.shape[1]
        num_mini_batches = num_samples // mini_batch_size
        for epoch_no in range(no_epochs):
            p = np.random.permutation(num_samples)
            X, Y = X[:, p], Y[p]
            for i in range(num_mini_batches + 1):
                running_counter += 1
                mini_batch_X = X[:, (i * mini_batch_size):min(i * mini_batch_size + mini_batch_size, num_samples)]
                mini_batch_Y = Y[(i * mini_batch_size):min(i * mini_batch_size + mini_batch_size, num_samples)]
                Y_hat = self.forward(mini_batch_X)
                self.back_propagation(mini_batch_Y)
                if rmsprop:
                    self.optimization_step_rmsprop(learning_rate, momentum_decay_rate)
                elif momentum_decay_rate < np.finfo(np.float32).eps:
                    self.optimization_step(learning_rate)
                else:
                    self.optimization_step_momentum(learning_rate, running_counter, momentum_decay_rate)
                running_cost += get_cost_value(Y_hat, mini_batch_Y)
            epoch_no_print = epoch_no + 1
            if epoch_no_print % print_every == 0:
                print(f"Epoch {epoch_no_print} - cost {running_cost / running_counter}")
                running_cost = 0
