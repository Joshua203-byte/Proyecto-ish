# Fine-Tuned Model: Job 3a259362-8a19-41f6-9b75-47a2390e64b5
This model was fine-tuned using the Home GPU Cloud infrastructure.

## Usage
```python
from peft import PeftModel, PeftConfig
from transformers import AutoModelForCausalLM

config = PeftConfig.from_pretrained('path/to/adapter')
model = AutoModelForCausalLM.from_pretrained(config.base_model_name_or_path)
model = PeftModel.from_pretrained(model, 'path/to/adapter')
```