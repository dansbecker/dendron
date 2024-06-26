---
title: Thinking and Talking
---

# 1. Building a Chat System with Dendron: Thinking and Talking

In the [Part 0](0_tutorial_single_node.md), we created a simple Dendron behavior tree with a single `CausalLMAction` node and used that tree to implement a chat loop. In this part of the tutorial, we will expand the capabilities of our agent by giving it the power of speech. This will require us to use Dendron's control flow capabilities, since we'll only want our agent to speak when it has something new to say. 

!!! tip

    Most of the current neural text-to-speech (TTS) models are a bit too slow, at least on consumer cards like the single 3090 I'm developing with. The one exception I've found is [Piper TTS](https://github.com/rhasspy/piper){:target="_blank"}, which I use in this tutorial. There are other neural models, like Suno's [Bark](https://github.com/suno-ai/bark){:target="_blank"} and Hugging Face's [Parler TTS](https://github.com/huggingface/parler-tts){:target="_blank"} that have great features you may want to check out, but they're slow enough on my hardware that I prefer Piper. If you want old-fashioned (non-neural) TTS, try replacing the `TTSAction` below with an action that uses the `pyttsx3` library.

If you find this tutorial too verbose and you just want to get the code, you can find the notebook for this part [here](https://github.com/RichardKelley/dendron-examples/blob/main/tutorial_1/part_1.ipynb){:target="_blank"}.

## Imports and Piper TTS

We'll start out by importing the libraries we need to implement TTS, beginning of course with Dendron:

```python linenums="1"
import dendron
from dendron.actions.causal_lm_action import CausalLMActionConfig, CausalLMAction
```

We import `CausalLMAction` as in Part 0 to create a chat node. We are going to create a custom `dendron.ActionNode` to implement our TTS capability, so next we import the components we need specifically for speech generation:

!!! tip

    Before you run this next block, you will need to pip install `piper-tts` if you have not already done so.

```python linenums="1"
import torch
from piper import PiperVoice
import numpy as np
import sounddevice as sd
```

Piper supports many voices, at several quality levels. You can find a [list of voices here](https://github.com/rhasspy/piper/blob/master/VOICES.md){:target="_blank"} and [demos of the voices here](https://rhasspy.github.io/piper-samples/){:target="_blank"}. We are going to use the voice named "Danny," which has only one quality setting (low). The quality levels refer to the number of model parameters. So-called "higher" quality models are just bigger. In spite of the name, the model we are going to use is quite good in my experience. It is also small enough that it runs in real time on the CPU.

You will need to download two files to use the Danny voice with Piper. To do so you can either follow the download link on the demo page linked above, or [get the files directly from Hugging Face](https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_US/danny/low){:target="_blank"}. You want `en_US-danny-low.onnx` and `en_US-danny-low.onnx.json`. Download these into the directory you're developing in, and be sure to double-check the file names when you save the files.

## Creating a Custom Dendron Action Node

We want to create an action node that generates some speech and actually says it. We'll show the whole node and then walk through the parts:

```python linenums="1"
class TTSAction(dendron.ActionNode):
    def __init__(self, name):
        super().__init__(name)
        self.voice = PiperVoice.load("en_US-danny-low.onnx", config_path="en_US-danny-low.onnx.json", use_cuda=False)
        
    def tick(self):
        try:
            input_text = self.blackboard["speech_in"]
            self.blackboard["speech_out"] = self.voice.synthesize_stream_raw("\t" + input_text, sentence_silence=0.1)
        except Exception as e:
            print("Speech generation exception: ", e)
            return dendron.NodeStatus.FAILURE

        return dendron.NodeStatus.SUCCESS
```

We can declare a new action node type by inheriting from `dendron.ActionNode`, which we do here. The parent class constructor requires us to specify a name for our node, so we take `name` as a parameter and forward that up to the parent in `super().__init__(name)`. Then we initialize our model. We specify the file names for the weights file and the config file - if you put these somewhere else make sure you change the strings you pass to `load`. We also specify `use_cuda=False`, which runs the model on the CPU. You can try setting this to `True`, but getting it to work may require that you play with version numbers for the dependencies we have installed so far.

The only member function we _need_ to define to implement a Dendron node is `tick(self)`. In general, a `tick` function should take no inputs and _must_ return a `NodeStatus`. In our case, we `try` to get some input text from `self.blackboard`, run the text through our model's `synthesize_stream_raw` function, and then write the output audio back to `self.blackboard`. If all goes well, we return `NodeStatus.SUCCESS`. If there's an exception, we print it out and then return `NodeStatus.FAILURE`. This is representative of the general flow of a `tick` function.

There are a few interesting details to note. We prepend the input text with a tab character (`\t`) because we have found during playback of the audio that sometimes the model doesn't correctly generate the very beginning of the audio stream. The tab seems to help with that. Similarly, the `sentence_silence=0.1` argument appends 100 milliseconds of silence to the end of each utterance. If you find this annoying, feel free to set it to its default of `0.0`.

## Pre- and Post-Tick Functions

The call to `synthesize_stream_raw` on line 9 above will generate the audio data we want to play, but won't in fact play a sound. To do that, we need to use the `sounddevice` library that we imported above. If our `TTSAction` class had a member function that used `sounddevice` then we'd be all set. You might imagine a function like `play_speech` that can play the sound data directly from memory (on Ubuntu at least):

```python linenums="1"
def play_speech(self):
    audio_stream = self.blackboard["speech_out"]
    for sent in audio_stream:
        audio = np.frombuffer(sent, dtype=np.int16)
        a = (audio - 32768) / 65536
        sd.play(a, 16000)
        sd.wait()
```

(The audio stream is broken down into chunks corresponding to Piper's best guess at sentence boundaries, and the arithmetic is necessary to switch from the data representation used by Piper to the representation used by `sounddevice`.)

After the `tick` function has returned, the audio data is stored in the blackboard and the `play_speech` function above could play it correctly. We just need a way to ensure that `play_speech` is called immediately after the `tick` function returns. It often happens that we want to execute code for its side effects immediately surrounding a `tick` call, and Dendron supports this with "pre-tick functions" and "post-tick functions." These are functions that get added as members of our node classes that are guaranteed to be called before and after a `tick`. Each `TreeNode` maintains a list of pre-tick and post-tick functions, and calls them in the order they are added. To see how this works, we first instantiate our node and then add our `play_speech` post-tick function to the node: 

```python linenums="1"
speech_node = TTSAction("speech_node")
speech_node.add_post_tick(play_speech)
```

Now that we've introduced pre- and post-tick functions into the mix, we can see that a more accurate depiction of a `tick` call looks something like the following:

<center>
<markdown figure>
![image](img/pre-post-tick.svg){:width="600px"}
</figure>
</center>

(It's an implementation detail, but these operations all take place inside of a method called `execute_tick` that is responsible for the sequence of operations in the figure above. You will never need to override `execute_tick` in your own node classes as long as you implement a reasonable `tick` operation and use pre- and post-tick functions correctly.)

With this, our `TTSAction` node is ready to go. It just needs something to say, so next we create a chat node.

## A Chat Node

To create our chat node, we will follow almost exactly the same steps as in the previous part. We'll start by creating a `CausalLMActionConfig` and then we'll use that configuration to instantiate a `CausalLMAction`. Then we'll define our input and output processor functions to translate between strings and the structured format that `openchat/openchat-3.5-0106` expects:

```python linenums="1"
chat_behavior_cfg = CausalLMActionConfig(load_in_4bit=True,
                                         max_new_tokens=128,
                                         do_sample=True,
                                         top_p=0.95,
                                         use_flash_attn_2=True,
                                         model_name='openchat/openchat-3.5-0106')

chat_node = CausalLMAction('chat_node', chat_behavior_cfg)

def chat_to_str(self, chat):
    return self.tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=True)

def str_to_chat(self, str):
    key = "GPT4 Correct Assistant:"
    idx = str.rfind(key)
    response = str[idx+len(key):]
    chat = self.blackboard[self.input_key]
    chat.append({"role" : "GPT4 Correct Assistant", "content" : response})
    return chat

chat_node.set_input_processor(chat_to_str)
chat_node.set_output_processor(str_to_chat)
```

So far this is identical to our previous chat system. But now we need to connect the output of our `chat_node` with the input of our `speech_node`. Having them communicate this information directly would violate the design constraint of behavior trees, so instead we'll have them communicate via their shared blackboard. Setting a blackboard is a side effecting operation, and post-tick functions are generally a good place to perform node operations that are partly or entirely used for their side effects, so we'll define a function `set_next_speech` and add it as a post-tick function for `chat_node`:

```python linenums="1"
def set_next_speech(self):
    text_output = self.blackboard["out"][-1]["content"]
    self.blackboard["speech_in"] = " " + text_output

chat_node.add_post_tick(set_next_speech)
```

Now our `chat_node` and our `speech_node` are completed. We just need to combine them into a single composite operation in a behavior tree.

## Composing Nodes with `Sequence`

In our new chat loop, we want our agent to read our input, generate a response with `chat_node`, and generate audio using `speech_node`. This implies a _sequential_ ordering to the `tick` operation for our tree. We can compose two or more nodes in sequence using a _control node_. Dendron provides two types of control nodes: `Fallback` and `Sequence`. We'll talk about `Fallback` in the [next part](2_tutorial_implicit_seq.md). A `Sequence` node keeps a list of children, and ticks them in order until either:

* One of the children returns `NodeStatus.FAILURE`, in which case the `Sequence` node fails, or
* All of the children return `NodeStatus.SUCCESS`, in which case the `Sequence` node succeeds.

We can compose our two nodes with a `Sequence` object and create a tree from the result as follows:

```pything linenums="1"
root_node = dendron.controls.Sequence("think_then_talk", [
    chat_node,
    speech_node
])

tree = dendron.BehaviorTree("talker_tree", root_node)
```

Both `Sequence` and `Fallback` reside in `dendron.controls`. A control node is like an action node in that its first argument is a string name. But the second argument to a control node is a list of children. The children are `tick`ed in the order they are given in the constructor. You can also add children dynamically to a control node after it is constructed. See the [`ControlNode` documentation](api/control_node.md){:target="_blank"} for details.

At this point our tree is ready for use. We can visually represent the tree as follows:

<center>
<markdown figure>
![image](img/1_adding_voice.svg)
</figure>
</center>

The `Sequence` node is represented by a rightward pointing arrow; this is standard in much of the behavior tree literature. The children of a control node should be read from left to right to understand the sequencing. The dark circle indicates the root. In this case calling the `tick` function will send a tick signal to the `think_then_talk` node first. This node will in turn first tick `chat_node`, and if `chat_node` returns `NodeStatus.SUCCESS` then `think_then_talk` will subsequently tick `speech_node`. This is precisely the behavior we wanted, and how we set up the flow of data through `tree.blackboard`.

!!! Tip

    This is the first time we have had to connect two nodes via a blackboard. It can be very helpful to think about blackboard state and `tick` operations in terms of pre-conditions and post-conditions. For each `TreeNode` that needs to communicate with other nodes, ask what state it requires from the blackboard to run its `tick` operation (pre-conditions) and what state it ensures will hold in the blackboard after its `tick` operation completes (post-conditions). I have found it helpful to "work backwards" from the end of a tree's tick logic to the beginning.

## The Chat Loop

Our agent is now ready to talk to us. Since we're still managing the chat state outside our behavior tree, you'll find that the logic is quite similar to the previous part:

```python linenums="1"
chat = []

while True:
    input_str = input("Input: ")
    chat.append({"role": "GPT4 Correct User", "content" : input_str})
    tree.blackboard["in"] = chat
    tree.tick_once()
    print("Output: ", tree.blackboard["out"][-1]["content"])
    if "Goodbye" in tree.blackboard["out"][-1]["content"]:
        break
```

If you've gotten to this point, congratulations! You have built a local chat agent that can talk to you. Not quite C-3PO, but I'd say pretty remarkable nonetheless.

## Conclusion

If you run our agent now, you'll find that you can type your end of the chat, but the agent speaks! Amazing. But if you play with this agent long enough, you'll find that its TTS capabilities are ... sometimes mixed. This appears to be common among neural TTS systems: they struggle with long outputs. If you play with the model long enough, you'll find that even with a limit on its output `chat_node` often generates strings that `speech_node` cannot speak. We'll see one way to (mostly) solve this problem in [part 3](3_tutorial_llm_conditional.md). But before we do that, we need to learn a powerful pattern in behavior tree design, which we'll introduce in [the next part](2_tutorial_implicit_seq.md) by moving the chat management logic into our behavior tree.
