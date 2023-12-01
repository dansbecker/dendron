from dataclasses import dataclass
from typing import Any 
from copy import deepcopy

@dataclass
class BlackboardEntryMetadata:
    key : str
    description : str
    type_constructor : type

    print_len: int = 16

    def __str__(self) -> str:
        key_field = f"{self.key:{self.print_len}.{self.print_len}}"
        desc_field = f"{self.description:{self.print_len}.{self.print_len}}"
        type_name = str(self.type_constructor)
        type_field = f"{type_name:{self.print_len}.{self.print_len}}"
        return f"{key_field} | {desc_field} | {type_field}"

class Blackboard:

    def __init__(self):
        self.entry_mapping = {}
        self.value_mapping = {}
        self.print_len = 16

    def set_print_len(self, new_len):
        if new_len <= 0:
            raise ValueError("print length must be positive")
        self.print_len = new_len
        for key, entry in self.entry_mapping.items():
            entry.print_len = new_len 

    def register_entry(self, entry : BlackboardEntryMetadata):
        self.entry_mapping[entry.key] = entry

    def get_entry(self, key):
        return self.entry_mapping[key]

    def set_entry(self, key, description = None, type_constructor = None):
        if not key in self.entry_mapping.keys():
            raise KeyError(f"{new_entry.key} not in blackboard.")
        old_entry = self.entry_mapping[key]
        new_entry = deepcopy(old_entry)
        if description is not None:
            new_entry.description = description
        if type_constructor is not None:
            new_entry.type_constructor = type_constructor
        self.entry_mapping[key] = new_entry

    def __getitem__(self, key):
        if not key in self.entry_mapping.keys():
            raise KeyError(f"Entry {key} not in blackboard.")
        target_type = self.entry_mapping[key].type_constructor
        temp_value = self.value_mapping[key]
        if type(temp_value) != target_type:
            return target_type(temp_value)
        else:
            return self.value_mapping[key]

    def get(self, key):
        return self.__getitem__(key)

    def __delitem__(self, key):
        del self.value_mapping[key]
        del self.entry_mapping[key]

    def __setitem__(self, key, value):
        if key not in self.entry_mapping.keys():
            new_entry = BlackboardEntryMetadata(key, "Autogenerated entry", type(value))
            self.register_entry(new_entry)
        self.value_mapping[key] = value 

    def set(self, key, value):
        self.__setitem__(key, value)

    def __iter__(self):
        return iter(self.value_mapping)

    def __len__(self):
        return len(self.value_mapping)

    def __str__(self):
        key_header_field = f"{'Key':{self.print_len}.{self.print_len}}"
        desc_header_field = f"{'Description':{self.print_len}.{self.print_len}}"
        type_header_field = f"{'Type':{self.print_len}.{self.print_len}}"
        value_header_field = f"{'Value':{self.print_len}.{self.print_len}}"
        bb_str = f"{key_header_field} | {desc_header_field} | {type_header_field} | {value_header_field} |\n"
        bb_str += f"{'=' * (self.print_len * 4 + 11)}\n"
        for key, value in self.value_mapping.items():
            entry = self.entry_mapping[key]
            value_string = str(value)
            value_field = f"{value_string:{self.print_len}.{self.print_len}}"
            bb_str += f"{str(entry)} | {value_field} | \n"

        return bb_str 

    
