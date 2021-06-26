class_name = object_dic[_class_token]
for key, value in object_dic.items():
    if key != _class_token:
        attr = key
        if isinstance(value, dict) and (_class_token in value):
            object_value = MyJson._generate_instance(value)
        else:
            object_value = value
        setattr(instance, f"_{class_name}{attr}", object_value)
