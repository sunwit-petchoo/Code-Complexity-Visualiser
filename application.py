from flask import Flask, url_for, render_template, request, flash, redirect, jsonify
from werkzeug.utils import secure_filename
import os, lizard, operator, json
import pickle
from sklearn.ensemble import RandomForestClassifier

# instantiate the app
app = Flask(__name__)
app.config.from_object(__name__)

UPLOAD_FOLDER = '.'
ALLOWED_EXTENSIONS = set(['js'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#Function: find matching statement
def find_matching_statement(f_all_lines, l_num, result_dict, level):
    con_statements = ["if", "else", "switch", "for", "while"]
    found = 0
    for con in con_statements:
        find_con = f_all_lines[l_num].find(con)
        if find_con >= 0:
            if con == "if" or con == "else":
                ck_else_if = f_all_lines[l_num].find("else if")
                if ck_else_if >= 0:
                    continue
            found += 1
            result_dict["condition"] = con
            result_dict["start line"] = l_num + 1
            result_dict["nested level"] = level
            break
        else:
            upper_line = l_num - 1
            find_con = f_all_lines[upper_line].find(con)
            if find_con >= 0:
                if con == "if" or con == "else":
                    ck_else_if = f_all_lines[upper_line].find("else if")
                    if ck_else_if >= 0:
                        continue
                found += 1
                result_dict["condition"] = con
                result_dict["start line"] = upper_line + 1
                result_dict["nested level"] = level
                break
    return result_dict if found > 0 else 0

#Function: visual matching statement
def visual_matching_statement(f_all_lines, l_num, result_dict, level):
    con_statements = ["if", "else", "switch", "for", "while"]
    found = 0
    for con in con_statements:
        find_con = f_all_lines[l_num].find(con)
        if find_con >= 0:
            if con == "if" or con == "else":
                ck_else_if = f_all_lines[l_num].find("else if")
                if ck_else_if >= 0:
                    continue
            found += 1
            visual_line = l_num + 1
            result_dict["name"] = con + " (line: " + str(visual_line) + ")"
            result_dict["parent"] = l_num + 1
            result_dict["children"] = level
            break
        else:
            upper_line = l_num - 1
            find_con = f_all_lines[upper_line].find(con)
            if find_con >= 0:
                if con == "if" or con == "else":
                    ck_else_if = f_all_lines[upper_line].find("else if")
                    if ck_else_if >= 0:
                        continue
                found += 1
                visual_line_up = upper_line + 1
                result_dict["name"] = con + " (line: " + str(visual_line_up) + ")"
                result_dict["parent"] = upper_line + 1
                result_dict["children"] = level
                break
    return result_dict if found > 0 else 0

#Function: remove {} from list
def pop_list(pop_index, remove_list):
    remove_list.pop(pop_index)
    remove_list.pop(pop_index)
    return remove_list

#Function: find next {} of list
def find_next_brace(cur_index, check_list):
    cur_index += 1
    check_list_sp = check_list[cur_index].split("_")
    result_val = check_list_sp[1]
    return result_val

#Function: find nested level
def find_nested_level(t_func_line, f_start_line, f_all_lines):
    # count {} for nested level
    c_list = []
    nested_level = 0
    result_key = ["condition", "start line", "nested level"]
    result_dict = dict.fromkeys(result_key, "")
    result_list = []
    line_counter = 0
    for _ in range(t_func_line):
        line_counter += 1
        if line_counter > t_func_line:
            break
        cur_line = f_all_lines[f_start_line]
        cur_line_strip = cur_line.strip()
        ck_block_comment_st = cur_line_strip.find("/*")
        if ck_block_comment_st >= 0:

            op_brace = cur_line_strip.find("{")
            cl_brace = cur_line_strip.find("}")
            if op_brace != -1 and op_brace < ck_block_comment_st:
                op_brace_w_line = str(f_start_line) + "_L"
                c_list.append(op_brace_w_line)
            if cl_brace != -1 and cl_brace < ck_block_comment_st:
                cl_brace_w_line = str(f_start_line) + "_R"
                c_list.append(cl_brace_w_line)

            ck_block_comment_end = cur_line_strip.find("*/")
            if ck_block_comment_end >= 0:
                f_start_line += 1
                continue
            else:
                while ck_block_comment_end < 0:
                    f_start_line += 1
                    line_counter += 1
                    cur_line = f_all_lines[f_start_line]
                    cur_line_strip = cur_line.strip()
                    ck_block_comment_end = cur_line_strip.find("*/")
                f_start_line += 1
                line_counter += 1
                cur_line = f_all_lines[f_start_line]
                cur_line_strip = cur_line.strip()

        op_brace = cur_line_strip.find("{")
        cl_brace = cur_line_strip.find("}")
        line_cmt = cur_line_strip.find("//")
        if op_brace >= 0:
            if op_brace < line_cmt or line_cmt < 0:
                op_brace_w_line = str(f_start_line)+"_L"
                c_list.append(op_brace_w_line)
        if cl_brace >= 0:
            if cl_brace < line_cmt or line_cmt < 0:
                cl_brace_w_line = str(f_start_line)+"_R"
                c_list.append(cl_brace_w_line)
        f_start_line += 1

    if c_list.__len__() != 0:
        c_list.pop()
        c_list.pop(0)

    c_list_index = 0
    while c_list.__len__() != 0:
        cur_val = c_list[c_list_index].split("_")
        l_num = int(cur_val[0])
        brace = cur_val[1]
        if brace == "L":
            next_brace = find_next_brace(c_list_index, c_list)
            if next_brace == "R":
                result_dict = find_matching_statement(f_all_lines, l_num, result_dict, "0")
                if result_dict != 0:
                    result_dict_copy = result_dict.copy()
                    result_list.append(result_dict_copy)
                else:
                    result_dict = dict.fromkeys(result_key, "")

                c_list = pop_list(c_list_index, c_list)
                c_list_index = 0
            else:
                while next_brace != "R":
                    c_list_index += 1
                    nested_level += 1
                    next_brace = find_next_brace(c_list_index, c_list)
                cur_val = c_list[c_list_index].split("_")
                l_num = int(cur_val[0])
                result_dict = find_matching_statement(f_all_lines, l_num, result_dict, str(nested_level))
                nested_level = 0
                if result_dict != 0:
                    result_dict_copy = result_dict.copy()
                    result_list.append(result_dict_copy)
                else:
                    result_dict = dict.fromkeys(result_key, "")

                c_list = pop_list(c_list_index, c_list)
                c_list_index = 0

    return result_list

#Function: count frequency of conditional statement
def count__func_conditional(t_func_line, f_start_line, f_all_lines):
    keys = ["if", "else", "switch", "for", "while"]
    val = []
    fq_if = 0
    fq_else = 0
    fq_switch = 0
    fq_for = 0
    fq_while = 0
    line_counter = 0
    for _ in range(t_func_line):
        line_counter += 1
        if line_counter > t_func_line:
            break
        cur_line = f_all_lines[f_start_line]
        # count condition phase
        cur_line_strip = cur_line.strip()
        ck_block_comment_st = cur_line_strip.find("/*")
        if ck_block_comment_st >= 0:
            ck_block_comment_end = cur_line_strip.find("*/")
            if ck_block_comment_end >= 0:
                f_start_line += 1
                continue
            else:
                while ck_block_comment_end < 0:
                    f_start_line += 1
                    line_counter += 1
                    cur_line = f_all_lines[f_start_line]
                    cur_line_strip = cur_line.strip()
                    ck_block_comment_end = cur_line_strip.find("*/")
                f_start_line += 1
                line_counter += 1
                cur_line = f_all_lines[f_start_line]
                cur_line_strip = cur_line.strip()

        for con in keys:
            ck_line_comment = cur_line_strip.find("//")
            if ck_line_comment != 0:
                index = cur_line_strip.find(con)
                if index < ck_line_comment or ck_line_comment < 0:
                    if index == 0 or index == 1:
                        if con == "if":
                            fq_if += 1
                        elif con == "else":
                            ck_elif = cur_line_strip.find("else if")
                            if ck_elif == -1:
                                fq_else += 1
                        elif con == "switch":
                            fq_switch += 1
                        elif con == "for":
                            fq_for += 1
                        elif con == "while":
                            fq_while += 1

        f_start_line += 1
    # add value for dict
    val.append(fq_if)
    val.append(fq_else)
    val.append(fq_switch)
    val.append(fq_for)
    val.append(fq_while)
    # pair key and value
    fq_dict = dict(zip(keys, val))
    val.clear()
    return fq_dict

#Function: visualise nested level
def visual_nested_level(t_func_line, f_start_line, f_all_lines):
    # count {} for nested level
    c_list = []
    nested_level = 0
    result_key = ["name", "parent", "children"]
    result_dict = dict.fromkeys(result_key, "")
    result_list = []
    line_counter = 0
    for _ in range(t_func_line):
        line_counter += 1
        if line_counter > t_func_line:
            break
        cur_line = f_all_lines[f_start_line]
        cur_line_strip = cur_line.strip()
        ck_block_comment_st = cur_line_strip.find("/*")
        if ck_block_comment_st >= 0:

            op_brace = cur_line_strip.find("{")
            cl_brace = cur_line_strip.find("}")
            if op_brace != -1 and op_brace < ck_block_comment_st:
                op_brace_w_line = str(f_start_line) + "_L"
                c_list.append(op_brace_w_line)
            if cl_brace != -1 and cl_brace < ck_block_comment_st:
                cl_brace_w_line = str(f_start_line) + "_R"
                c_list.append(cl_brace_w_line)

            ck_block_comment_end = cur_line_strip.find("*/")
            if ck_block_comment_end >= 0:
                f_start_line += 1
                continue
            else:
                while ck_block_comment_end < 0:
                    f_start_line += 1
                    line_counter += 1
                    cur_line = f_all_lines[f_start_line]
                    cur_line_strip = cur_line.strip()
                    ck_block_comment_end = cur_line_strip.find("*/")
                f_start_line += 1
                line_counter += 1
                cur_line = f_all_lines[f_start_line]
                cur_line_strip = cur_line.strip()

        op_brace = cur_line_strip.find("{")
        cl_brace = cur_line_strip.find("}")
        line_cmt = cur_line_strip.find("//")
        if op_brace >= 0:
            if op_brace < line_cmt or line_cmt < 0:
                op_brace_w_line = str(f_start_line)+"_L"
                c_list.append(op_brace_w_line)
        if cl_brace >= 0:
            if cl_brace < line_cmt or line_cmt < 0:
                cl_brace_w_line = str(f_start_line)+"_R"
                c_list.append(cl_brace_w_line)
        f_start_line += 1

    if c_list.__len__() != 0:
        c_list.pop()
        c_list.pop(0)

    c_list_index = 0
    while c_list.__len__() != 0:
        cur_val = c_list[c_list_index].split("_")
        l_num = int(cur_val[0])
        brace = cur_val[1]
        if brace == "L":
            next_brace = find_next_brace(c_list_index, c_list)
            if next_brace == "R":
                result_dict = find_matching_statement_for_graph(f_all_lines, l_num, result_dict, "0")
                if result_dict != 0:
                    result_dict_copy = result_dict.copy()
                    result_list.append(result_dict_copy)
                else:
                    result_dict = dict.fromkeys(result_key, "")

                c_list = pop_list(c_list_index, c_list)
                c_list_index = 0
            else:
                while next_brace != "R":
                    c_list_index += 1
                    nested_level += 1
                    next_brace = find_next_brace(c_list_index, c_list)
                cur_val = c_list[c_list_index].split("_")
                l_num = int(cur_val[0])
                result_dict = find_matching_statement_for_graph(f_all_lines, l_num, result_dict, str(nested_level))
                nested_level = 0
                if result_dict != 0:
                    result_dict_copy = result_dict.copy()
                    result_list.append(result_dict_copy)
                else:
                    result_dict = dict.fromkeys(result_key, "")

                c_list = pop_list(c_list_index, c_list)
                c_list_index = 0

    return result_list

#Function: find_matching_statement_for_graph
def find_matching_statement_for_graph(f_all_lines, l_num, result_dict, level):
    con_statements = ["if", "else", "switch", "for", "while"]
    found = 0
    for con in con_statements:
        find_con = f_all_lines[l_num].find(con)
        if find_con >= 0:
            if con == "if" or con == "else":
                ck_else_if = f_all_lines[l_num].find("else if")
                if ck_else_if >= 0:
                    continue
            found += 1
            actual_line = l_num+1
            result_dict["condition"] = con + " (Line: "+str(actual_line)+")"
            result_dict["start line"] = l_num + 1
            result_dict["nested level"] = level
            break
        else:
            upper_line = l_num - 1
            find_con = f_all_lines[upper_line].find(con)
            if find_con >= 0:
                if con == "if" or con == "else":
                    ck_else_if = f_all_lines[upper_line].find("else if")
                    if ck_else_if >= 0:
                        continue
                found += 1
                actual_line2 = upper_line+1
                result_dict["condition"] = con + " (Line: "+str(actual_line2)+")"
                result_dict["start line"] = upper_line + 1
                result_dict["nested level"] = level
                break

    return result_dict if found > 0 else 0

#Function: find_nested_next
def find_next_nested(cur_index, nested_list):
    cur_index += 1
    next_nested = nested_list[cur_index]
    return next_nested

#Function: find_nested_parent
def find_nested_parent(cur_index, nested_list, cur_lvl):
    con_search = True
    search_lvl = cur_lvl - 1
    pre_nested = []
    while con_search:
        cur_index -= 1
        pre_nested = nested_list[cur_index]
        pre_lvl = int(pre_nested.get("nested level"))
        if pre_lvl == search_lvl:
            break
    return pre_nested

#check file
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


#Upload file
@app.route("/", methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash("No file part")
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            global test
            test = file.filename
            return redirect(url_for('results'))
    return render_template('index.html')

#result
@app.route('/results')
def results():
    #read file
    #print(test)
    #i = lizard.analyze_file("test.txt")
    i = lizard.analyze_file(test)
    filename = os.path.basename(i.filename)
    fList = i.function_list

    #Result
    #--Cyclomatic_complexity for each function
    ccList = []
    for jsFunction in fList:
        ccNo = jsFunction.cyclomatic_complexity
        risk = ""
        if ccNo <= 10:
            risk = "Without Much Risk"
        elif ccNo > 10 and ccNo <= 20:
            risk = "Moderate Risk"
        elif ccNo > 20 and ccNo <= 50:
            risk = "High Risk"
        elif ccNo > 50:
            risk = "Very High Risk"

        dict1 =	{
            "function": jsFunction.name,
            "cc_no": str(jsFunction.cyclomatic_complexity),
            "risk": risk
        }
        ccList.append(dict1)
    
    #--Cyclomatic_complexity for entire file
    cc_avg = i.average_cyclomatic_complexity
    risk_avg = ""
    if cc_avg <= 10:
        risk_avg = "Without Much Risk"
    elif cc_avg > 10 and ccNo <= 20:
        risk_avg = "Moderate Risk"
    elif cc_avg > 20 and ccNo <= 50:
        risk_avg = "High Risk"
    elif cc_avg > 50:
        risk_avg = "Very High Risk"

    #--Cyclomatic_complexity Visualisation
    bar_labels = []
    bar_values = []
    line_values = []
    for jsFunction in fList:
        bar_values.append(str(jsFunction.cyclomatic_complexity))
        bar_labels.append(jsFunction.name)
    for _ in bar_values:
        line_values.append(round(cc_avg, 2))
    
    #--Function Details Visualisation
    fn_labels = []
    nloc_values = []
    for jsFunction in fList:
        nloc_values.append(str(jsFunction.nloc))
        fn_labels.append(jsFunction.name)

    #--Nested Level & Count Conditional
    fn_details = []
    nestedTreeList = []
    nestedTreeDict = {"name": filename, "parent": "null"}
    nestedTreeDict_copy = nestedTreeDict.copy()
    nestedTreeList.append(nestedTreeDict_copy)
    #--List for conditional statement graph
    ifList = []
    switchList = []
    forList = []
    whileList = []
    for jsFunction in fList:
        fTotalLine = jsFunction.end_line - jsFunction.start_line + 1
        fStartLineR = jsFunction.start_line - 1
        jsFile = open(test, "r")
        allLines = jsFile.readlines()
        nestedList = find_nested_level(fTotalLine, fStartLineR, allLines)
        nestedList.sort(key=operator.itemgetter('start line'))

        #nested graph
        nestedResult = visual_nested_level(fTotalLine, fStartLineR, allLines)
        nestedResult.sort(key=operator.itemgetter('start line'))
        
        
        nestedIndex = 0
        for nestedListTree in nestedResult:
            nameNode = nestedListTree.get("condition")
            lvlNode = int(nestedListTree.get("nested level"))
            parent = ""
            if lvlNode == 0:
                parent = filename
            else:
                parentList = find_nested_parent(nestedIndex, nestedResult, lvlNode)
                parent = parentList.get("condition")
            nestedTreeDict["name"] = nameNode
            nestedTreeDict["parent"] = parent
            nestedTreeDict_copy = nestedTreeDict.copy()
            nestedTreeList.append(nestedTreeDict_copy)
            nestedIndex += 1
        

        freqConditionCount = count__func_conditional(fTotalLine, fStartLineR, allLines)
        #--List for conditional statement graph
        ifList.append(freqConditionCount.get("if"))
        switchList.append(freqConditionCount.get("switch"))
        forList.append(freqConditionCount.get("for"))
        whileList.append(freqConditionCount.get("while")) 
        jsFile.close()
        var = 0
        for line in range(fTotalLine):
            # print(allLines[fStartLineR])
            # check var for same line pattern
            checkLine = allLines[fStartLineR]
            checkLineStrip = checkLine.strip()
            # print(checkLineStrip)
            countStatement = checkLineStrip.count(";")
            # print("count--st" + str(countStatement))
            searchVar = checkLineStrip.find("var")
            if searchVar == 0:
                if countStatement > 1:
                    statementList = checkLineStrip.split(";")
                    for statement in statementList:
                        if statement != "":
                            startVar = statement.find("var")
                            if startVar == 0:
                                findCom = statement.find(",")
                                if findCom >= 0:
                                    vListStatement = statement.split(",")
                                    var += vListStatement.__len__() - 1
                else:
                    searchCom = checkLineStrip.find(",")
                    if searchCom >= 0:
                        vList = checkLineStrip.split(",")
                        var += vList.__len__() - 1
            lineList = allLines[fStartLineR].split()
            var += lineList.count("var")

            # print(lineList)
            # check var in for loop such as counter for(vari=0;i++)
            for subLine in lineList:
                # print(subLine.find("(var"))
                if subLine.find("(var") >= 0:
                    var += 1
                if subLine.find(";var") >= 0:
                    var += 1
            fStartLineR += 1
        dict_fnDetails = {
            "fnName": jsFunction.name,
            "noOfLine_total": str(fTotalLine),
            "startLine": str(jsFunction.start_line),
            "endLine": str(jsFunction.end_line),
            "noOfLine": str(jsFunction.nloc),
            "noOfVars": str(var),
            "pars": str(jsFunction.parameters),
            "conditionCount": freqConditionCount,
            "nestedList": nestedList
        }
        fn_details.append(dict_fnDetails)

    #print(nestedTreeList)
    #Nested Tree
    nestedTreeList = json.dumps(nestedTreeList)
    print(nestedTreeList)

    #Call result html
    return render_template('result.html', fileName = filename, 
    ccList = ccList, cc_avg = round(cc_avg, 2), risk_avg = risk_avg,
    labels=bar_labels, values=bar_values, line_values=line_values,
    fn_labels=fn_labels, nloc_values=nloc_values, fn_details=fn_details,
    nestedTreeList=nestedTreeList, ifList=ifList, switchList=switchList,
    forList=forList,  whileList=whileList)
    

@app.route("/predict", methods=['GET', 'POST'])
def predict():
    #load model
    #model_knn = pickle.load(open('model_knn.pkl', 'rb'))
    model_cart = pickle.load(open('model_cart.pkl', 'rb'))

    #For rendering results on HTML GUI
    data = [[178,1,99,1,26,9,1077]]
    prediction = model_cart.predict(data)
    print(prediction)
    return render_template('predict.html')

if __name__ == "__main__":
    app.run(debug=True)