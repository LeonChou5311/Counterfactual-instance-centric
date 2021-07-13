# -*- coding: utf-8 -*-
"""DiCE_Final.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1yvp1_eVyZzr2r8zsNlnXrHw1E1V7tu5y

# DiCE/ LIME/ confusion matrix
"""

!pip3 install tensorflow

############# Initialise on Google Colab 

from google.colab import drive
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from google.colab import auth
from oauth2client.client import GoogleCredentials
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from google.colab import auth
from oauth2client.client import GoogleCredentials 
drive.mount('/content/gdrive', force_remount=True)
auth.authenticate_user()
gauth = GoogleAuth()
gauth.credentials = GoogleCredentials.get_application_default()
gdrive = GoogleDrive(gauth)
gdrive.CreateFile({"id": "1wwSN3AIl_dmayKENu5jnc1BRaNPe8BZc"}).GetContentFile("learning.py")

############# install package
!pip install dice_ml
!pip install alibi
!pip install pyAgrum

# Commented out IPython magic to ensure Python compatibility.
############# import the library
import tensorflow as tf
import dice_ml
import pandas as pd
tf.get_logger().setLevel(40) # suppress deprecation messages
#tf.compat.v1.disable_v2_behavior() # disable TF2 behaviour as alibi code still relies on TF1 constructs
from tensorflow.keras.layers import Dense, Input
from tensorflow.keras.models import Model, load_model
from tensorflow.keras.utils import to_categorical
import matplotlib
# %matplotlib inline
import matplotlib.pyplot as plt
import numpy as np
import os
from sklearn.datasets import load_boston
import pandas as pd
from sklearn.preprocessing import OneHotEncoder, StandardScaler,MinMaxScaler
from learning import encode_data 
from learning import *
print('TF version: ', tf.__version__)
print('Eager execution enabled: ', tf.executing_eagerly()) # False
seed = 123
tf.random.set_seed(seed)
np.random.seed(seed)

"""## **Load Diabetes dataset**"""

from google.colab import drive 
# drive.mount('/content/gdrive') 
data=pd.read_csv('gdrive/My Drive//Counterfactual-prototype-main/datasets/diabetes.csv')

# Giving current root path
# PATH = "./"
PATH = "gdrive/My Drive//Counterfactual-prototype-main/"
# PATH = "/Counterfactual-prototype-main/"
# name of dataset
DATASET_NAME = "diabetes.csv"

# variable containing the class labels in this case the dataset contains:
# 0 - if not diabetes
# 1 - if diabetes
class_var = "Outcome"

# load dataset
dataset_path = PATH + "datasets/" + DATASET_NAME
data = pd.read_csv( dataset_path )

# features
feature_names = data.drop([class_var], axis=1).columns.to_list()

# balance dataset
sampled_data = data.sample(frac=1)
sampled_data = sampled_data[ sampled_data["Outcome"] == 0]

no_data = sampled_data.sample(frac=1)[0:268]
yes_data = data[ data["Outcome"] == 1]

balanced_data = [no_data,yes_data]
balanced_data = pd.concat(balanced_data)

# apply one hot encoder to data
# standardize the input between 0 and 1
X, Y, encoder, scaler = encode_data( balanced_data, class_var)

n_features = X.shape[1]
n_classes = len(data[class_var].unique())

# load existing training data
print("Loading training data...")
X_train, Y_train, X_test, Y_test, X_validation, Y_validation= load_training_data( dataset_path )

print("====================Features====================")
print(feature_names)
print("================================================")

# the best performing model was obtained with 5 hidden layers with 12 neurons each
model_name = "model_h5_N12"

# specify paths where the blackbox model was saved
path_serialisation_model = PATH + "training/" + DATASET_NAME.replace(".csv", "") + "/model/" 
path_serialisation_histr = PATH + "training/" + DATASET_NAME.replace(".csv", "") + "/history/" 

# load model and model performance history
print("Loading Blackbox model...")
model_history = load_model_history( model_name, path_serialisation_histr )
model = load_model( model_name, path_serialisation_model )

# check modelxw
model.summary()

"""## **Load trained model**"""

# the best performing model was obtained with 5 hidden layers with 12 neurons each
model_name = "model_h5_N12"

# specify paths where the blackbox model was saved
path_serialisation_model = PATH + "training/" + DATASET_NAME.replace(".csv", "") + "/model/" 
path_serialisation_histr = PATH + "training/" + DATASET_NAME.replace(".csv", "") + "/history/" 

# load model and model performance history
print("Loading Blackbox model...")
model_history = load_model_history( model_name, path_serialisation_histr )
model = load_model( model_name, path_serialisation_model )

# check modelxw
model.summary()

from enum import Enum
class PredictionType(Enum):
  TruePositive = "TruePositive"
  TrueNegative = "TrueNegative"
  FalsePositive = "FalsePositive"
  FalseNegative = "FalseNegative"
  
class AllPacks(object):
  '''
  Class for storing cases in different prediction type

  '''
  def __init__(self, true_positives,true_negatives, false_positives, false_negatives):
    # constructor
    self.true_positives = true_positives
    self.true_negatives = true_negatives
    self.false_positives = false_positives
    self.false_negatives = false_negatives
  def __len__(self,):
    return len(self.true_positives)\
    +len(self.true_negatives)\
    +len(self.false_positives)\
    +len(self.false_negatives)
    
  def true_positives_len(self,):
    return len(self.true_positives)

  def get_len(self, p_t):
    if p_t == PredictionType.TruePositive:
      return self.true_positives_len()
    elif p_t == PredictionType.TrueNegative:
      return self.true_negatives_len()
    elif p_t == PredictionType.FalsePositive:
      return self.false_positives_len()
    elif p_t == PredictionType.FalseNegative:
      return self.false_negatives_len()
    else:
      raise NotImplemented('This prediction type is unsupported.');

  def true_negatives_len(self,):
    return len(self.true_negatives)
  
  def false_negatives_len(self,):
    return len(self.false_negatives)
  
  def false_positives_len(self,):
    return len(self.false_positives)

  def get_instance(self, p_t, index):
    if p_t == PredictionType.TruePositive:
      return self.get_true_positive(index)
    elif p_t == PredictionType.TrueNegative:
      return self.get_true_negative(index)
    elif p_t == PredictionType.FalsePositive:
      return self.get_false_positive(index)
    elif p_t == PredictionType.FalseNegative:
      return self.get_false_nagative(index)
    else:
      raise NotImplemented('This prediction type is unsupported.');

  def get_true_positive(self, index = 0):
    try:
      return self.true_positives[index]
    except:
      raise ValueError("Input index out of range, true positive only have [%d] cases" % (self.true_positives_len()))
  def get_true_negative(self, index = 0):
    try:
      return self.true_negatives[index]
    except:
      raise ValueError("Input index out of range, true negative only have [%d] cases" % (self.true_negatives_len()))
  def get_false_positive(self, index = 0):
    try:
      return self.false_positives[index]
    except:
      raise ValueError("Input index out of range, true positive only have [%d] cases" % (self.false_positives_len()))
  def get_false_nagative(self, index = 0):
    try:
      return self.false_negatives[index]
    except:
      raise ValueError("Input index out of range, true positive only have [%d] cases" % (self.false_negatives_len()))



from copy import deepcopy
from time import time
class DiCECounterfactaulWrapper(object):
  '''
  Wrapper class to generate DiCE cf
  '''
  def __init__(self, dice_explainer):
    self.dice_explainer__ =  dice_explainer
  
  def run_counterfactual_print_result(self, case):
    return_case = deepcopy(case)
    # print_block("", "Finding counterfactuals...")
    input_data = np.array([case["original_vector"]])
    start_time = time()
    input_df = pd.DataFrame(input_data,columns=feature_names)
    self.input_df = input_df
    dice_exp = self.dice_explainer__.generate_counterfactuals(input_df, total_CFs=3,desired_class="opposite",
                                                              #proximity_weight=1.5, diversity_weight=1.0
                                                              )
    self.dice_exp = dice_exp
    end_time = time()
    time_took = end_time - start_time
    # print_block("Time Took", "%.3f sec" % (time_took))
    if len(dice_exp.final_cfs_df) == 0:
      # print_block("", "No counterfactaul found!")
      return_case['cf'] = [None] * input_data.shape[1]
    else:  
      # counterfactual = scaler.inverse_transform(list())
      return_case['cf'] = list(dice_exp.final_cfs_df.iloc[0][:-1])

    return_case['time'] = time_took
    # self.print_counterfactual_results(case, counterfactual)
    return return_case

  def print_counterfactual_results(self, case, counterfactual):
    print_block("Prediction type", case["prediction_type"], mark_times=7)
    print_block("Black box prediction", case["predictions"], mark_times=3)
    print_block("Ground truth", case["ground_truth"], mark_times= 5)
    print_block("Oringal input", pd.DataFrame([case["original_vector"]], columns=feature_names),mark_times = 60)
    print_block("Counterfactual", pd.DataFrame(counterfactual, columns=feature_names), mark_times=60)

diabetes_feature_range = (X_train.min(axis=0), X_train.max(axis=0))
# store all information 
local_data_dict = generate_local_predictions( X_test, Y_test, model, scaler, encoder )
# sorting by different conditions
true_positives,true_negatives, false_positives, false_negatives = wrap_information( local_data_dict )
# get packs
all_packs = AllPacks(true_positives,true_negatives, false_positives, false_negatives)

##### Utils #####
def print_block(title, content, mark_times=20):
  upper_line = mark_times*("=") + title + mark_times*("=")
  bottom_line = len(upper_line) *"="
  print(upper_line)
  if (type(content) == pd.DataFrame):
    display(content)
  else:
    print("| \t" + str(content))
  print(bottom_line)
  print("\n")

class People:
  def __init__(self, name):
    self.name = name
    self.call_my_name()

  def call_my_name(self,):
    print(f"I'm {self.name} !!")

leon = People('Leon')
leon.call_my_name()

class KeepOneValue(tf.keras.layers.Layer):
    def __init__(self,):
        super(KeepOneValue, self).__init__()

    def call(self, inputs):
        return inputs[:, 1:2]

seq = tf.keras.Sequential(
    [
        model,
        KeepOneValue(),
    ]
)



target_name = "Outcome"
feature_names = list(balanced_data.columns)
feature_names.remove(target_name)

# all black box predictions
all_predictions = encoder.inverse_transform( model.predict( X_test ) )



# Dataset for training an ML model
temp_df = pd.DataFrame(X, columns=feature_names)
temp_df[target_name] = Y[:, 1]
d = dice_ml.Data(dataframe=balanced_data, continuous_features=feature_names, outcome_name=target_name)
# Pre-trained ML model
m = dice_ml.Model(model=seq, backend="TF2")
# DiCE explanation instance
exp = dice_ml.Dice(d,m)

dice_wrapper = DiCECounterfactaulWrapper(exp)

dice_wrapper.run_counterfactual_print_result(all_packs.get_true_negative(3))

a = 5
print("a is %d "% (a))

output_column_names= [ f'orgin_{f}' for f in feature_names] + [ f'cf_{f}' for f in feature_names] + ['time(sec)'] + ["prediction_type"]
def generate_df_for_all(packs, cf_func):
  ### Create an empty dataframe for appending data.
  result_df = pd.DataFrame({}, columns= output_column_names)

  ### Loop through each predict type.
  for p_t in [PredictionType.TruePositive, PredictionType.TrueNegative, PredictionType.FalsePositive, PredictionType.FalseNegative]:
    print_block("","Doing %s" % p_t.value)

    ### Get the length, so we can through all the instance in this predict type.
    total_length = packs.get_len(p_t)
    
    ### Loop through all the instance in this predict type.
    for i in range(total_length):

      print_block("Instance %d" %i, "Running...")

      ### Get the result (including counterfactal and running time) from the cf_func.
      returned_case = cf_func(packs.get_instance(p_t, i))

      ### Using the information from returned_case to create a dataframe (for appending to result_df).
      df_i = pd.DataFrame([
      returned_case["original_vector"] + returned_case['cf'] + [returned_case['time'], returned_case['prediction_type']]],columns=output_column_names)

      ### appending the current result to the total result dataframe.
      result_df = result_df.append(df_i)
  return result_df

dice_cf_df = generate_df_for_all(all_packs, dice_wrapper.run_counterfactual_print_result)

dice_cf_df.to_csv('dice_cf_df_cf3.csv')

## read the csv
try_load_dice_cf_df = pd.read_csv('dice_cf_df_cf3.csv')

list(dice_wrapper.dice_exp.final_cfs_df.iloc[0][:-1])

# Commented out IPython magic to ensure Python compatibility.
# %ipython history -g

# Commented out IPython magic to ensure Python compatibility.
# %history -g
