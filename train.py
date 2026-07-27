# Founder AI - Unsloth Fine-Tuning Script
# Designed for Google Colab (with free T4 GPU) or any PyTorch GPU environment.
#
# To run this in Colab:
# 1. Create a new notebook with GPU runtime (T4 GPU).
# 2. Upload 'dataset.json' and this 'train.py' script.
# 3. Run a cell with:
#    !pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
#    !pip install --no-deps trl peft loralib sentencepiece subword-nmt
#    !python train.py

import os
import torch
from unsloth import FastLanguageModel
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments

# Configuration
max_seq_length = 2048  # Supports RoPE scaling automatically
dtype = None           # None for auto detection (Float16/Bfloat16 depending on GPU)
load_in_4bit = True    # Use 4bit quantization to fit on free T4 GPUs

# 1. Load Model & Tokenizer
print("Loading model and tokenizer...")
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "unsloth/Llama-3.2-3B-Instruct-bnb-4bit", # Or "unsloth/llama-3-8b-Instruct-bnb-4bit"
    max_seq_length = max_seq_length,
    dtype = dtype,
    load_in_4bit = load_in_4bit,
)

# 2. Setup LoRA PEFT Parameters
print("Configuring LoRA adapters...")
model = FastLanguageModel.get_peft_model(
    model,
    r = 16, # Rank (higher rank = more capacity, but more memory)
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                      "gate_proj", "up_proj", "down_proj"],
    lora_alpha = 16,
    lora_dropout = 0, # Optimized by Unsloth
    bias = "none",    # Optimized by Unsloth
    use_gradient_checkpointing = "unsloth", # 2x longer context windows, less VRAM
    random_state = 3407,
    use_rslora = False,
    loftq_config = None,
)

# 3. Format dataset for instruction tuning
# Standard Llama 3.2 Chat Template format
alpaca_prompt = """Below is an instruction that describes a task. Write a response that appropriately completes the request.

### Instruction:
{}

### Response:
{}"""

EOS_TOKEN = tokenizer.eos_token
def formatting_prompts_func(examples):
    instructions = examples["instruction"]
    inputs       = examples["input"]
    outputs      = examples["output"]
    texts = []
    for instruction, input_val, output in zip(instructions, inputs, outputs):
        # Join instruction and input if input exists
        full_instruction = instruction
        if input_val:
            full_instruction += f"\nContext/Input:\n{input_val}"
            
        text = alpaca_prompt.format(full_instruction, output) + EOS_TOKEN
        texts.append(text)
    return { "text" : texts }

print("Loading dataset.json...")
if not os.path.exists("dataset.json"):
    raise FileNotFoundError("dataset.json not found in the current directory. Please upload it first.")

dataset = load_dataset("json", data_files="dataset.json", split="train")
dataset = dataset.map(formatting_prompts_func, batched = True)

# 4. Configure Trainer
print("Setting up Trainer...")
trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = dataset,
    dataset_text_field = "text",
    max_seq_length = max_seq_length,
    dataset_num_proc = 2,
    packing = False, # Can speed up training for short sequences
    args = TrainingArguments(
        per_device_train_batch_size = 2,
        gradient_accumulation_steps = 4,
        warmup_steps = 5,
        max_steps = 60, # 193 samples, batch size 8 = ~24 steps per epoch. 60 steps is ~2.5 epochs
        learning_rate = 2e-4,
        fp16 = not torch.cuda.is_bf16_supported(),
        bf16 = torch.cuda.is_bf16_supported(),
        logging_steps = 1,
        optim = "adamw_8bit",
        weight_decay = 0.01,
        lr_scheduler_type = "linear",
        seed = 3407,
        output_dir = "outputs",
    ),
)

# 5. Start Training
print("Starting training...")
trainer_stats = trainer.train()
print("Training completed successfully!")

# 6. Save GGUF local model
# We save in both q8_0 (highly accurate 8-bit quantization) and q4_k_m (fast, memory-friendly 4-bit)
print("Saving model to GGUF format...")

print("Exporting q8_0 GGUF...")
model.save_pretrained_gguf("founder_ai_model_q8", tokenizer, quantization_method = "q8_0")

print("Exporting q4_k_m GGUF...")
model.save_pretrained_gguf("founder_ai_model_q4", tokenizer, quantization_method = "q4_k_m")

print("Fine-tuning pipeline completed. GGUF models saved under 'founder_ai_model_q8' and 'founder_ai_model_q4' directories.")
