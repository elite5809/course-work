from numpy import mean
from numpy import std
from numpy import squeeze
# from matplotlib import pyplot
# from sklearn.model_selection import KFold
from keras.datasets import mnist
from tensorflow.keras.utils import to_categorical
from keras.models import Sequential
from keras.layers import Conv2D
from keras.layers import MaxPooling2D
from keras.layers import Dense
from keras.layers import Flatten
from tensorflow.keras.optimizers import SGD
from numpy import argmax

def load_dataset():
    # Use mnist.load_data() to retrieve data. Ensure you have imported mnist from keras. datasets
    (trainX, trainY), (testX, testY) = mnist.load_data()
    #reshape the data into 1-d
    trainX = trainX.reshape((trainX.shape[0], 28, 28, 1))
    testX = testX.reshape((testX.shape[0], 28, 28, 1))
    #Convert the output numbers to categorical values
    trainY = to_categorical(trainY)
    testY = to_categorical(testY)
    return trainX, trainY, testX, testY

# define cnn model
def define_model():
    model = Sequential()
    model.add(Conv2D(32, (3, 3), activation='relu', kernel_initializer='he_uniform', input_shape=(28, 28, 1)))
    model.output_shape
    model.add(MaxPooling2D((2, 2)))
    model.add(Flatten())
    model.add(Dense(100, activation='relu', kernel_initializer='he_uniform'))
    model.add(Dense(10, activation='softmax'))
    # compile model
    opt = SGD(learning_rate=0.01, momentum=0.9)
    model.compile(optimizer=opt, loss='categorical_crossentropy', metrics=['accuracy'])
    return model

def evaluate_model(trainDataX, trainDataY, testDataX, testDataY):
    # define model
    model = define_model()
    model.summary()
    # fit model
    history = model.fit(trainDataX, trainDataY, epochs=10, batch_size=32, validation_data=(testDataX, testDataY), verbose=1)
    # evaluate model
    _, acc = model.evaluate(testDataX, testDataY, verbose=1)
    print('> %.3f' % (acc * 100.0))
    return model

def prep_pixels(train, test):
    # convert from integers to floats
    train_norm = train.astype('float32')
    test_norm = test.astype('float32')
    # normalize to range 0-1
    train_norm = train_norm / 255.0
    test_norm = test_norm / 255.0
    # return normalized images
    return train_norm, test_norm

def workflow():
    trainX, trainY, testX, testY = load_dataset()
    trainX, testX = prep_pixels(trainX, testX)
    trained_model = evaluate_model(trainX, trainY, testX, testY)
    # visualize_misclass(trained_model, testX, testY)

workflow()