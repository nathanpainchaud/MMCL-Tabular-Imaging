from torch.utils.data import DataLoader
from pytorch_lightning import Trainer
from datasets.ImageDataset import ImageDataset
from datasets.TabularDataset import TabularDataset
from models.Evaluator import Evaluator
from utils.utils import grab_arg_from_checkpoint, seed_everything


def test(hparams, wandb_logger=None):
  """
  Tests trained models. 
  
  IN
  hparams:      All hyperparameters
  """
  seed_everything(hparams)
  
  if hparams.datatype == 'imaging' or hparams.datatype == 'multimodal':
    test_dataset = ImageDataset(hparams.data_test_eval_imaging, hparams.labels_test_eval_imaging, hparams.delete_segmentation, 0, grab_arg_from_checkpoint(hparams, 'img_size'), target=hparams.target, train=False, live_loading=hparams.live_loading, task=hparams.task, multi_channel=hparams.get('multi_channel_imaging', False))
    
    print(test_dataset.transform_val.__repr__())
  elif hparams.datatype == 'tabular':
    test_dataset = TabularDataset(hparams.data_test_eval_tabular, hparams.labels_test_eval_tabular, hparams.eval_one_hot, hparams.field_lengths_tabular)
    hparams.input_size = test_dataset.get_input_size()
  else:
    raise Exception('argument dataset must be set to imaging, tabular or multimodal')
  
  drop = ((len(test_dataset)%hparams.batch_size)==1)

  test_loader = DataLoader(
    test_dataset,
    num_workers=hparams.num_workers, batch_size=hparams.batch_size,  
    pin_memory=True, shuffle=False, drop_last=drop, persistent_workers=bool(hparams.num_workers))

  hparams.dataset_length = len(test_loader)

  model = Evaluator(hparams)
  model.freeze()
  trainer = Trainer.from_argparse_args(hparams, gpus=1, logger=wandb_logger)
  # Don't need to provide `ckpt_path` when calling `trainer.test` since weights are already loaded
  # when instantiating the model in the `Evaluator(hparams)` call
  trainer.test(model, test_loader)