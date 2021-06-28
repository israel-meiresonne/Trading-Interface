class_name = object_dic[_class_token]
for key, value in object_dic.items():
    if key != _class_token:
        attr = key
        object_value = MyJson._root_decoding(value)
        setattr(instance, attr, object_value)
