import os, re, inspect, json

from . import classes


def read_lattice_file(filepath):
    latticename = os.path.basename(filepath)
    with open(filepath) as file:
        lines = re.sub('[ \t]', '', file.read()).splitlines()
        lines = [line for line in lines if line and line[0] != '#']

        # devide lines into elementname, type, parameter and comment
        length = len(lines)
        objectname = [''] * length
        type = [''] * length
        parameters = [''] * length
        comments = [''] * length
        following_lines = []
        starting_line = 0
        for i, line in enumerate(lines):
            # save comments
            _split = line.split('#')
            if len(_split) > 1:
                comments[i] = _split[1]
            _split = _split[0]

            # divide into starting and following lines
            _split = _split.split(':')
            if len(_split) > 1:
                starting_line = i
                objectname[i] = _split[0]
                _split = _split[1].split(',', maxsplit=1)
                type[i] = _split[0]
                parameters[i] = _split[1]
            else:
                following_lines.append(i)
                parameters[starting_line] += _split[0]
                if comments[i]:
                    comments[starting_line] += ' ' + comments[i]

        # delete following lines (in reverse order)
        for i in following_lines[::-1]:
            del objectname[i]
            del comments[i]
            del parameters[i]

        # create and execute string
        lis = [f'{objectname[i]} = {type[i]}("{objectname[i]}", {parameters[i]}, comment="{comments[i]}")' for i in
               range(len(objectname))]
        string = '\n'.join(lis)
        # print(string)
        exec(string)
        return list(locals().values())[-1]


def from_json(json_data):
    objects = {}  # dictionary for all objects (elements + lines)
    for k, v in json_data['elements'].items():
        type_ = v.pop('type')
        class_ = getattr(classes, type_)
        objects[k] = class_(name=k, **v)
    for cell_name, elements_name_list in json_data['cells'].items():
        objects[cell_name] = classes.Cell(name=cell_name)
    for cell_name, elements_name_list in json_data['cells'].items():
        tree = [objects[name] for name in elements_name_list]
        objects[cell_name].tree_add_objects(tree)

    main_tree = [objects[name] for name in json_data["main_cell"]]
    return classes.MainCell(name=json_data["name"], tree=main_tree, description=json_data.get("description", ""))


def read_lattice_file_json(file_path):
    with open(file_path) as f:
        json_data = json.load(f)
    return from_json(json_data)


def save_lattice_file_json(main_cell, file_path=None):
    file_path = file_path if file_path else f"{main_cell.name}.json"
    # dirname = os.path.dirname(file_path)
    # if not os.path.exists(dirname):
    #     os.makedirs(dirname)
    with open(file_path, 'w') as outfile:
        json.dump(as_dict(main_cell), outfile, indent=2)


def as_dict(main_cell):
    elements_dict = {}
    for element in main_cell.elements.values():
        tmp = {key: getattr(element, key) for (key, value) in inspect.signature(element.__class__).parameters.items()}
        tmp.pop("name")
        elements_dict[element.name] = tmp
        elements_dict[element.name]["type"] = element.__class__.__name__

    cells_dict = {cell.name: [obj.name for obj in cell.tree] for cell in main_cell.cells.values()}
    main_dict = dict(name=main_cell.name, description=main_cell.description, elements=elements_dict, cells=cells_dict, main_cell=[obj.name for obj in main_cell.tree])
    return main_dict


def as_json(main_cell, indent=None):
    return json.dumps(as_dict(main_cell), indent=indent)