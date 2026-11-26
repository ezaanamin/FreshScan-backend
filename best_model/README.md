# YOLO11 Multiclass Produce & Grocery Detection (v2)

This folder contains the best trained weights and validation results from the `yolo11_multiclass_v2` training run.

## Performance Summary

- **mAP50**: `0.889` (88.9%)
- **mAP50-95**: `0.676` (67.6%)
- **Precision**: `0.860` (86.0%)
- **Recall**: `0.841` (84.1%)
- **Trained Epochs**: 120
- **Model Architecture**: YOLO11n (2.59M parameters)

## Top Classes (AP50)

- `guava_rotten`: 0.995
- `mango_rotten`: 0.995
- `package`: 0.995
- `guava`: 0.994
- `pomegranate`: 0.988
- `apple_rotten`: 0.985
- `orange_rotten`: 0.984
- `pomegranate_rotten`: 0.982
- `onion`: 0.977
- `apple`: 0.961
- `banana_rotten`: 0.953
- `mango`: 0.951
- `garlic`: 0.948
- `potato`: 0.942
- `tomato_rotten`: 0.936
- `eggs`: 0.926
- `lemon`: 0.925
- `butter`: 0.877
- `orange`: 0.878
- `tomato`: 0.852
- `strawberry_rotten`: 0.806
- `banana`: 0.780
- `capsicum`: 0.757
- `capsicum_rotten`: 0.722
- `strawberry`: 0.689
- `nut`: 0.659
- `bolt`: 0.557

---

## Contents of this Folder

- `best.pt`: PyTorch weights of the best checkpoint.
- `multiclass_detect_stratified.yaml`: Dataset configuration with class mapping (27 classes).
- `results.png` & `results.csv`: Training and validation loss curves across 120 epochs.
- `confusion_matrix.png` & `confusion_matrix_normalized.png`: Class-level confusion matrices.
- `BoxF1_curve.png`, `BoxPR_curve.png`, `BoxP_curve.png`, `BoxR_curve.png`: PR, F1, and Precision/Recall curve plots.
- `val_batch*_pred.jpg`: Visual validation sample predictions with bounding boxes.
- `args.yaml`: Exact hyperparameter configuration used during training.

---

## How to Use `best.pt`

### Python Inference
```python
from ultralytics import YOLO

# Load model
model = YOLO("best.pt")

# Predict
results = model.predict(
    source="path/to/image_or_video",
    conf=0.50,
    iou=0.45,
    save=True
)
```

### CLI Inference
```bash
python -m ultralytics predict model=best.pt source=path/to/image.jpg conf=0.50 save=True
```
