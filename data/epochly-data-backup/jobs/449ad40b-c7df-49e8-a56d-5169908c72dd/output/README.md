# Fine-Tuned Model: Job 449ad40b-c7df-49e8-a56d-5169908c72dd
This model was fine-tuned using the Home GPU Cloud infrastructure.

## Usage
```python
from peft import PeftModel, PeftConfig
from transformers import AutoModelForCausalLM

config = PeftConfig.from_pretrained('path/to/adapter')
model = AutoModelForCausalLM.from_pretrained(config.base_model_name_or_path)
model = PeftModel.from_pretrained(model, 'path/to/adapter')
```