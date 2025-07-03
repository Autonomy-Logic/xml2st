


def ComputeInterface(self, pou):
        interface = pou.getinterface()
        if interface is not None:
            if self.Type == "FUNCTION":
                returntype_content = interface.getreturnType()[0]
                returntype_content_type = returntype_content.getLocalTag()
                if returntype_content_type == "derived":
                    self.ReturnType = returntype_content.getname()
                else:
                    self.ReturnType = returntype_content_type.upper()
            for varlist in interface.getcontent():
                variables = []
                located = []
                varlist_type = varlist.getLocalTag()
                for var in varlist.getvariable():
                    vartype_content = var.gettype().getcontent()
                    if vartype_content.getLocalTag() == "derived":
                        var_type = vartype_content.getname()
                        blocktype = self.GetBlockType(var_type)
                        if blocktype is not None:
                            self.ParentGenerator.GeneratePouProgram(var_type)
                            variables.append((var_type, var.getname(), None, None))
                        else:
                            self.ParentGenerator.GenerateDataType(var_type)
                            initial = var.getinitialValue()
                            if initial is not None:
                                initial_value = initial.getvalue()
                            else:
                                initial_value = None
                            address = var.getaddress()
                            if address is not None:
                                located.append((vartype_content.getname(), var.getname(), address, initial_value))
                            else:
                                variables.append((vartype_content.getname(), var.getname(), None, initial_value))
                    else:
                        var_type = var.gettypeAsText()
                        initial = var.getinitialValue()
                        if initial is not None:
                            initial_value = initial.getvalue()
                        else:
                            initial_value = None
                        address = var.getaddress()
                        if address is not None:
                            located.append((var_type, var.getname(), address, initial_value))
                        else:
                            variables.append((var_type, var.getname(), None, initial_value))
                if varlist.getconstant():
                    option = "CONSTANT"
                elif varlist.getretain():
                    option = "RETAIN"
                elif varlist.getnonretain():
                    option = "NON_RETAIN"
                else:
                    option = None
                if len(variables) > 0:
                    self.Interface.append((varTypeNames[varlist_type], option, False, variables))
                if len(located) > 0:
                    self.Interface.append((varTypeNames[varlist_type], option, True, located))


def GetVariableType(self, name):
        parts = name.split('.')
        current_type = None
        if len(parts) > 0:
            name = parts.pop(0)
            for _list_type, _option, _located, vars in self.Interface:
                for var_type, var_name, _var_address, _var_initial in vars:
                    if name == var_name:
                        current_type = var_type
                        break
            while current_type is not None and len(parts) > 0:
                blocktype = self.ParentGenerator.Controler.GetBlockType(current_type)
                if blocktype is not None:
                    name = parts.pop(0)
                    current_type = None
                    for var_name, var_type, _var_modifier in blocktype["inputs"] + blocktype["outputs"]:
                        if var_name == name:
                            current_type = var_type
                            break
                else:
                    tagname = ComputeDataTypeName(current_type)
                    infos = self.ParentGenerator.Controler.GetDataTypeInfos(tagname)
                    if infos is not None and infos["type"] == "Structure":
                        name = parts.pop(0)
                        current_type = None
                        for element in infos["elements"]:
                            if element["Name"] == name:
                                current_type = element["Type"]
                                break
        return current_type