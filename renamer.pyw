# coding=utf-8
import subprocess
import tempfile
from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox, scrolledtext

from dnd_wrapper import TkDND, _parse_list

import os
import shutil

tk=Tk()
rootdnd=TkDND(tk)
tk.title('REnamer')
tk.resizable(False, False)

procdir_var=IntVar(value=0)
msg_var=StringVar(value='拖拽文件到这里')
fns=[]  # [ ('c:/dir/to', 'file.txt'), ... ]

f=Frame(tk)
f.grid(row=0, column=0)

def do_rename(old, new):
    L=len(old)
    assert L==len(new)
    err=False

    for i in range(L):
        if old[i]==new[i]:
            continue
        try:
            if new[i]:
                os.makedirs(new[i][0], exist_ok=True)
                shutil.move(os.path.join(*old[i]), os.path.join(*new[i]))
            else:
                os.remove(os.path.join(*old[i]))
        except Exception as e:
            messagebox.showerror('REnamer', f'{repr(e)}\n\n{old[i]}\n{new[i]}')
            err=True

    return not err

def show_confirm_box(old, new):
    L=len(old)
    assert L==len(new)

    def callback():
        if do_rename(old, new):
            do_clear()
            msg_var.set('重命名完成')
            dialog.destroy()

    dialog=Toplevel(tk)
    dialog.title(f'确认重命名')
    dialog.rowconfigure(0, weight=1)
    dialog.columnconfigure(0, weight=1)
    dialog.focus_force()
    dialog.geometry('1300x700')

    t=scrolledtext.ScrolledText(dialog)
    t.grid(row=0, column=0, sticky='nswe')
    t.tag_configure('prefix', background='#ddd', foreground='#444')
    t.tag_configure('dir', background='#fff', foreground='#000')
    t.tag_configure('fn', background='#b7cbf7', foreground='#000')
    t.tag_configure('delete', background='#f2bcbc', foreground='#000')

    for i in range(L):
        if old[i]==new[i]:
            continue

        t.insert('end', ' < ', 'prefix', ' ')
        t.insert('end', old[i][0], 'dir', '/')
        t.insert('end', old[i][1], 'fn', '\n')

        t.insert('end', ' > ', 'prefix', ' ')
        if new[i]:
            t.insert('end', new[i][0], 'dir', '/')
            t.insert('end', new[i][1], 'fn', '\n\n')
        else:
            t.insert('end', ' 将被删除 ', 'delete', '\n\n')

    t['state']='disabled'

    Button(dialog, text='重命名', command=callback).grid(row=1, column=0, sticky='we')

def update_count():
    msg_var.set(f'已选择 {len(fns)} 个文件')

def do_drop(event):
    global fns

    for fn in _parse_list(tk, event.data):
        splited=os.path.split(fn)
        if splited not in fns:
            fns.append(splited)

    fns=sorted(fns)
    update_count()

def do_clear():
    fns.clear()
    update_count()

def do_proc(*_):
    editors=[
        '%programfiles%/notepad++/notepad++.exe',
        '%programfiles(x86)%/notepad++/notepad++.exe',
        '%ProgramW6432%/notepad++/notepad++.exe',
        '%systemroot%/system32/notepad.exe',
    ]
    procdir=procdir_var.get()

    def stringify(fns):
        return '\n'.join([(os.path.join(d, f).replace('\\', '/') if procdir else f) for d, f in fns])

    def parse(txt):
        lines=txt.split('\n')

        if len(lines)!=len(fns):
            messagebox.showerror('REnamer', '文件行数错误')
            raise RuntimeError(f'bad line count {len(lines)}')
        if procdir:
            for l in lines:
                if not os.path.isabs(l):
                    messagebox.showerror('REnamer', f'{l} 不是绝对路径')
                    raise RuntimeError(f'not absolute {l}')

        return [(
            (os.path.split(l) if procdir else (fns[ind][0], l))
            if l else None
        ) for ind, l in enumerate(lines)]

    for editor in editors:
        if os.path.isfile(os.path.expandvars(editor)):
            tmpfn=tempfile.mktemp('.filenames.txt')
            old_content=stringify(fns)
            with open(tmpfn, 'w') as f:
                f.write(old_content)

            subprocess.Popen(
                executable=os.path.expandvars('%systemroot%/system32/cmd.exe'),
                args='/c start /wait "" "%s" "%s"'%(os.path.expandvars(editor), tmpfn)
            ).wait()

            if os.path.isfile(tmpfn):
                with open(tmpfn, 'r') as f:
                    new_content=f.read()
                os.remove(tmpfn)
                if old_content!=new_content:
                    new_fns=parse(new_content)
                    show_confirm_box(fns, new_fns)
                else:
                    msg_var.set('文件没有修改')
            break
    else:
        messagebox.showerror('Renamer', '没有可用的外部编辑器')

Button(f, text='清空', command=do_clear, width=7).grid(row=0, column=0)
Button(f, text='重命名', command=do_proc, width=14).grid(row=0, column=1)
Checkbutton(f, text='包含路径', variable=procdir_var, onvalue=1, offvalue=0).grid(row=0, column=2)

Label(tk, textvariable=msg_var).grid(row=1, column=0, pady=30)

rootdnd.bindtarget(tk, do_drop, 'text/uri-list')

mainloop()
