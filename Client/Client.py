import socket
import tkinter as tk
import os
import time
import sys
import datetime
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog

HEADER = 4096
FORMAT = 'utf-8'
IP = socket.gethostbyname(socket.gethostname())
PORT = 65432
ADDR = (IP, PORT)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)

localIP, localPORT = client.getsockname()

isUploaded = False #Biến global theo dõi quá trình upload

root = tk.Tk()
#==================================================================================
isReceived = False #Biến global theo dõi quá trình download
stop_sending = '1'
#Biến toàn cục này nhằm lưu địa chỉ muốn lưu file
entry = None
directoryPath = ''
#Tổ chức cấu trúc cây để phân cấp thư mục. 
class Node:
    def __init__(self, fileName, size, dateModified):
        self.name = fileName
        self.size = size
        self.dateModified = dateModified
        self.children = []
    def add_child(self, newNode):
        self.children.append(newNode)
def receive_file(fileName):
    global stop_sending
    stop_sending = '1'
    def finish_progress():
        global isReceived
        # Đóng file
        fout.close()
                
        # Cập nhật thanh progress bar
        if totalBytes == sizeOfFile:
            progress_label.config(text='Download completed!')
            progress_bar["value"] = 100
            download_window.after(2000, download_window.destroy)
            isReceived = True
            print("Hàm trả về True")
            return True
        else:
            progress_label.config(text='Download failed!')
            download_window.after(2000, download_window.destroy)
            isReceived = False
            print("Hàm trả về False")
            return False
    def download_progress():
        # Dùng nonlocal để truy cập biến từ ngoài hàmơ
        global stop_sending
        send_message(stop_sending)
        if stop_sending == '0':
            return finish_progress()
        global isReceived
        nonlocal totalBytes, sizeOfFile
        if totalBytes >= sizeOfFile:
            return finish_progress()  # Kết thúc download nếu tải xong

        try:
     # Tin nhắn đầu tiên là độ dài của nội dung mà client có thể nhận
            fileLength = client.recv(HEADER).decode(FORMAT)
        
            if not fileLength:
                return finish_progress()   # Nếu fileLength rỗng, thoát vòng lặp
            fileLength = int(fileLength) #Chuyển kích thước dạng chuỗi về dạng số nguyên
        
            if fileLength == 0: #Đến khi hết dữ liệu thì không ghi nữa, thoát vòng lặp 
                return finish_progress() 
        
            data = client.recv(fileLength)
       
            if not data:    
                return finish_progress()  # Nếu không có dữ liệu, thoát vòng lặp
            fout.write(data)  # Ghi dữ liệu vào file
            #Tính tổng số bytes đã nhận
            totalBytes += len(data)
            #Khoảng thời gian
            duration = time.time() - start
        
            #Phần trăm hoàn thành
            process = (totalBytes/sizeOfFile)*100

            progress_bar["value"] = process
            percent_label.config(text=f"{process:.2f}%")
            download_window.update_idletasks()  # Cập nhật giao diện
            download_window.after(100,download_progress)  # Gọi lại hàm sau 100ms
            sys.stdout.write(f"\rProcess: {process:.2f}%")  # Hiển thị trên một dòng
            sys.stdout.flush()  # Cập nhật ngay lập tức
        except Exception as e:
            print(f"Error during Download: {e}")
            progress_label.config(text="Download Failed!")
            download_window.after(2000, download_window.destroy)
            return finish_progress()
    def handle_duplicate_file_name(fileName, saveDir):
        # Lấy tên file và phần mở rộng
        baseName, ext = os.path.splitext(fileName)
            
        # Đường dẫn đầy đủ của file
        newFileName = fileName
        counter = 1
            
        # Kiểm tra xem file đã tồn tại chưa, nếu có thì thêm số vào tên
        while os.path.exists(os.path.join(saveDir, newFileName)):
            newFileName = f"{baseName} ({counter}){ext}"
            counter += 1
            
        return newFileName   
    global directoryPath
    #Chờ tín hiệu bên server xem file có mở được không
    response = receive_message()
    if response == '-1':
        return
    global isReceived
    download_window = tk.Toplevel(root)  # Tạo hộp thoại mới
    download_window.title("Downloading...")
    download_window.geometry("400x150")
    def close_progress_bar_window():
        global stop_sending
        stop_sending = '0'
    download_window.protocol("WM_DELETE_WINDOW", close_progress_bar_window)  # Xử lý khi cửa sổ bị đóng

    # Thanh tiến trình
    progress_label = tk.Label(download_window, text="Downloading...", font=("Arial", 14))
    progress_label.pack(pady=10)

    progress_bar = ttk.Progressbar(download_window, orient="horizontal", mode="determinate", length=300)
    progress_bar.pack(pady=20)
    progress_bar["value"] = 0
    # Nhãn hiển thị phần trăm tiến trình
    percent_label = tk.Label(download_window, text="0%", font=("Arial", 12))
    percent_label.pack(pady=5)
            
    download_window.update_idletasks()  # Cập nhật giao diện

    temp = receive_message()
    try:
        sizeOfFile = int(temp)
    except:
        print(temp)
        return
    totalBytes = 0
    #Xử lí tên trùng
   
    filePath = os.path.join(directoryPath,fileName)
    fout = open(filePath,"wb")
    start = time.time()  # Thời điểm bắt đầu

    download_progress()
    download_window.wait_window()  #Chờ đóng
    return isReceived

#Hàm nhận theo preorder
def receive_preorder(root):
    try:
        #Nhận số con của root. 
        numChild = int(receive_message())
        #Nhận tham số tệp tin
        name = receive_message()
        size = int(receive_message())
        date = receive_message()
        print(f"{numChild} - {name} - {size} - {date}")
        # Nếu root chưa được khởi tạo
        if root.name is None:
            root.name = name
            root.size = size
            root.dateModified = date
            for i in range(numChild):
                receive_preorder(root)
        else:
            # Nếu root đã được khởi tạo => Tạo node mới và thêm vào danh sách con
            newNode = Node(name, size, date)
            root.add_child(newNode)
            root = newNode
            for i in range(numChild):
                receive_preorder(newNode)
    except Exception as error:
        print(f"{error}")

#Hàm dưới đây để tổ chức một tree view
def show_list_file():

    global entry
    global directoryPath
    send_message('view')
    directoryPath = ''
    def insert_node(tree, parent_id, node):
        node_size = node.size if node.size is not None else "Unknown"
        node_date = node.dateModified if node.dateModified is not None else "Unknown"

        node_id = tree.insert(
            parent_id, 
            "end", 
            text=node.name if node.name else "Unnamed Node",
            values=(node_size, node_date)
        )

        node_map[node_id] = node
        for child in node.children:
            insert_node(tree, node_id, child)
 


    def on_double_click(event):
        # Xử lý sự kiện double-click để nạp nút con
        selected_item = tree.selection()[0]  # Lấy ID của nút được chọn
        selected_node = node_map.get(selected_item)  # Tìm node tương ứng

        if selected_node and tree.get_children(selected_item) == ():  # Nếu chưa nạp con
            for child in selected_node.children:
                insert_node(tree, selected_item, child)
    #Xử lí sự kiện nhấn nút
    def on_button_click():
        global entry
        global directoryPath
        # Lấy ID của nút được chọn
        selected_item = tree.selection()
        if not selected_item:
            print("No item selected")
            return
        selected_item = selected_item[0]

        # Lấy node tương ứng
        selected_node = node_map.get(selected_item)

        # Kiểm tra loại node
        if selected_node:
            if not selected_node.children: #Nếu nó không có con (Nghĩa là file)
               if not directoryPath == '': #Nếu đã chọn fileName và đã chọn thư mục 
                    entry.delete(0, tk.END)  # Xóa nội dung cũ trong ô nhập
                    entry.insert(0, f'download {selected_node.name}')# Thêm chuỗi download {file_path} vào ô nhập tin nhắn 
                    list_window.destroy()
               else:
                   messagebox.showinfo("Thông báo", "Please select folder to save file", parent = list_window)
               
    def selection_file_button_click():
        global directoryPath
        directoryPath = ''
        directoryPath = filedialog.askdirectory(title = "Select folder to save file", parent = list_window)
        if directoryPath:
           messagebox.showinfo("Thông báo", f"Folder selected: {directoryPath}", parent = list_window) #Đặt parent = list_window nhằm ngăn không cho nó minimize

    # Nhận dữ liệu
    root_node = Node(None, None, None)
    receive_preorder(root_node)
    # Tạo cửa sổ hiển thị
    list_window = tk.Toplevel()
    list_window.title("TreeView Example")
    list_window.geometry("600x400")
    # Đặt chế độ modal để ngăn cửa sổ bị minimize
    list_window.grab_set()
     #list_window.protocol("WM_DELETE_WINDOW",on_button_click) 
    # Khung chứa TreeView và thanh cuộn
    frame = tk.Frame(list_window)
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    # Định nghĩa các cột
    columns = ("Size", "Date Modified")
    tree = ttk.Treeview(frame, columns=columns, show="tree headings", height=15)
    tree.pack(side="left", fill="both", expand=True)

    # Đặt tiêu đề các cột
    tree.heading("#0", text="Name", anchor="w")  # Cột gốc (hiển thị tên)
    tree.heading("Size", text="Size", anchor="center")
    tree.heading("Date Modified", text="Date Modified", anchor="center")

    # Đặt độ rộng cột
    tree.column("#0", width=250, anchor="w")  # Cột tên
    tree.column("Size", width=100, anchor="center")  # Cột kích thước
    tree.column("Date Modified", width=150, anchor="center")  # Cột ngày sửa đổi

    # Thêm thanh cuộn dọc
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")

    # Thêm nút thực hiện hành động
    button_frame = tk.Frame(list_window)
    button_frame.pack(fill="x", padx=10, pady=(0, 10))

    selection_file_button = tk.Button(button_frame, text="Select File to download", font = ('Arial',13), command=on_button_click)
    selection_file_button.pack(side="right")

    select_folder_button = tk.Button(button_frame, text="Select Folder to save", font = ('Arial', 13), command = selection_file_button_click)
    select_folder_button.pack(side="left")

    # Bản đồ lưu trữ tham chiếu giữa TreeView và Node
    node_map = {}
    # Thêm root node và các con của nó
    insert_node(tree, "", root_node)

    # Gắn sự kiện Double Click
    tree.bind("<Double-1>", on_double_click)

#==================================================================================



def receive_message():
    msgContent = '-1'
    msgLength = int(client.recv(HEADER).decode(FORMAT))
    msgContent = client.recv(msgLength).decode(FORMAT)
    return msgContent

def send_message(msg):
    msgContent = msg.encode(FORMAT)
    msgLength = len(msgContent) 
    sendLength = str(msgLength).encode(FORMAT)
    sendLength += b' '*(HEADER - len(sendLength))
    client.send(sendLength)
    client.send(msgContent)

def client_login(username, password):
    if username and password:
        send_message(username)
        send_message(password)
        res = client.recv(1).decode(FORMAT)
        if res=='1':
            return True, username
        else:
            return False, None
    else:
        return False, None

def main(username):
    global entry
    root.title("GUI")
    for widget in root.winfo_children():
        widget.destroy()

    check_botton_upload = False
    choose_upload_frame = None
    def choose_upload():
        nonlocal check_botton_upload
        nonlocal choose_upload_frame

        def choose_file():
            file_path = filedialog.askopenfilename(title="Select File to Upload")  # Mở File Explorer để chọn file
            if file_path:  # Nếu người dùng chọn file
                entry.delete(0, tk.END)  # Xóa nội dung cũ trong ô nhập
                entry.insert(0, f'upload {file_path}')  # Thêm chuỗi upload {file_path} vào ô nhập tin nhắn

                choose_upload_frame.destroy()
                check_botton_upload=False

        def choose_folder():
            folderPath = filedialog.askdirectory(title="Select Folder to Upload")
            if folderPath:
                entry.delete(0, tk.END)  # Xóa nội dung cũ trong ô nhập
                entry.insert(0, f'upload {folderPath}')  # Thêm chuỗi upload {file_path} vào ô nhập tin nhắn
                
                choose_upload_frame.destroy()
                check_botton_upload=False

        if not check_botton_upload:
            check_botton_upload=True
            
            choose_upload_frame = tk.Frame(root)
            choose_upload_frame.pack(side="top", anchor='center', pady = 5)

            upload_file_button = tk.Button(choose_upload_frame, text="Upload File", font=("Arial", 13), command=choose_file)
            upload_file_button.pack(side="left", anchor='center', fill="x")

            upload_folder_button = tk.Button(choose_upload_frame, text="Upload Folder", font=("Arial", 13), command=choose_folder)
            upload_folder_button.pack(side="left", anchor='center', fill="x", padx=100)
        else:
            choose_upload_frame.destroy()
            check_botton_upload=False
    
    def normalize_input(request):
        #Loại bỏ kí tự, khoảng trắng thừa đầu, cuối
        request = request.strip()
        
        #Tách thành 2 phần (Hoặc 1 phần)
        parts = request.split(maxsplit = 1)
        command = ""
        path = ""
        warn=""

        if len(parts) < 2:
            command=parts[0]
        else:
            command = parts[0]
            path = parts[1]

            if path.startswith('"') and path.endswith('"'):
                path = path[1:-1]
            
            if command=="upload":
                if not os.path.exists(path):
                    warn="Your path isn't exists"

        return command, path, warn

    def upload_file(filePath):
            upload_window = tk.Toplevel(root)  # Tạo hộp thoại mới
            upload_window.title("Uploading...")
            upload_window.geometry("400x150")
            
            # Thanh tiến trình
            progress_label = tk.Label(upload_window, text="Uploading...", font=("Arial", 14))
            progress_label.pack(pady=10)

            progress_bar = ttk.Progressbar(upload_window, orient="horizontal", mode="determinate", length=300)
            progress_bar.pack(pady=20)
            progress_bar["value"] = 0
            # Nhãn hiển thị phần trăm tiến trình
            percent_label = tk.Label(upload_window, text="0%", font=("Arial", 12))
            percent_label.pack(pady=5)
            
            upload_window.update_idletasks()  # Cập nhật giao diện

            try:
                fin = open(filePath, "rb")
            except:
                print("Cannot open this file")
                return False
            
            sizeOfFile = os.path.getsize(filePath)  # Lấy kích thước file
            totalBytes = 0  # Tính toán tổng số bytes đã tải
            startTime = time.time()  # Thời điểm bắt đầu
            
            def finish_progress():
                global isUploaded
                # Gửi tín hiệu kết thúc file
                sendLength = str(0).encode(FORMAT)
                sendLength += b' ' * (HEADER - len(sendLength))
                client.send(sendLength)
                
                response = client.recv(2048).decode(FORMAT)
                print(f"\n[SERVER RESPONSE]: {response}")
                
                # Đóng file
                fin.close()
                
                # Cập nhật thanh progress bar
                if totalBytes == sizeOfFile:
                    progress_label.config(text='Upload completed!')
                    progress_bar["value"] = 100
                    upload_window.after(2000, upload_window.destroy)
                    isUploaded = True
                    return True
                else:
                    progress_label.config(text='Upload failed!')
                    upload_window.after(2000, upload_window.destroy)
                    isUploaded = False
                    return False
                
            
            def upload_progress():
                        # Dùng nonlocal để truy cập biến từ ngoài hàm
                nonlocal totalBytes, sizeOfFile
                if totalBytes >= sizeOfFile:
                    return finish_progress()  # Kết thúc upload nếu tải xong

                try:
                    data = fin.read(HEADER)  # Đọc tối đa 1KB mỗi lần
                    if not data:
                        return finish_progress()  # Nếu không còn dữ liệu, kết thúc
                    
                    finLength = len(data)
                    sendLength = str(finLength).encode(FORMAT)
                    sendLength += b' ' * (HEADER - len(sendLength))
                    client.send(sendLength)
                    client.send(data)

                    totalBytes += len(data)
            
                    process = (totalBytes / sizeOfFile) * 100
                    progress_bar["value"] = process
                    percent_label.config(text=f"{process:.2f}%")
                    upload_window.update_idletasks()  # Cập nhật giao diện
                    upload_window.after(100,upload_progress)  # Gọi lại hàm sau 100ms
                    sys.stdout.write(f"\rProcess: {process:.2f}%")  # Hiển thị trên một dòng
                    sys.stdout.flush()  # Cập nhật ngay lập tức
                except Exception as e:
                    print(f"Error during upload: {e}")
                    progress_label.config(text="Upload Failed!")
                    upload_window.after(2000, upload_window.destroy)
                    return finish_progress()
                
            upload_progress()
            upload_window.wait_window()  # Chờ cửa sổ tải lên đóng
            return isUploaded

    def upload_folder(folderPath):
        try:
            # Gửi lệnh upload_folder kèm theo tên thư mục gốc
            folder_name = os.path.basename(folderPath)
            send_message(folder_name)  # Gửi tên thư mục gốc
            # Duyệt qua toàn bộ thư mục và gửi các file/folder
            for root, dirs, files in os.walk(folderPath):
                for dir_name in dirs:
                    dir_path = os.path.relpath(os.path.join(root, dir_name), folderPath)
                    send_message(dir_path)  # Gửi đường dẫn thư mục
                    send_message("FOLDER")  # Gửi tín hiệu là thư mục

                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    relative_path = os.path.relpath(file_path, folderPath)
                    send_message(relative_path)  # Gửi đường dẫn file
                    send_message("FILE")         # Gửi tín hiệu là file

                    # Gửi nội dung file
                    with open(file_path, "rb") as f:
                        while chunk := f.read(HEADER):
                            chunk_size = len(chunk)
                            client.send(f"{chunk_size}".encode(FORMAT).ljust(HEADER))
                            client.send(chunk)

                    client.send(f"{0}".encode(FORMAT).ljust(HEADER))  # Tín hiệu kết thúc file

            send_message("END")  # Tín hiệu kết thúc quá trình upload
            print("Folder uploaded successfully!")
            isUploaded = True
            return isUploaded
        except Exception as e:
            print(f"Error uploading folder: {e}")
            isUploaded = False
            return isUploaded

    def ib_message(event=None):
        global entry
        message = entry.get()
        if message.isspace():
            entry.delete(0, tk.END)
        elif (message=="logout" or message=="LOGOUT"):
            send_message(message)
            root.after(2000, lambda: menu_login())
        elif message:
            # Tạo label chứa tin nhắn và thêm vào vùng cuộn
            message = entry.get()
            # Tạo label chứa tin nhắn và thêm vào vùng cuộn
            message_frame = tk.Frame(scrollable_frame, bg="white")
            message_frame.pack(side="top", fill="x",pady=(0, 3))
            
            now = datetime.datetime.now()

            # Tạo Label cho tin nhắn, căn phải
            label_time = tk.Label(message_frame, text=f" [{now.hour}:{now.minute} - {now.day}/{now.month}/{now.year}] ", font=("Arial", 15, "bold"), bg="white", bd=0, anchor="w")
            label_time.pack(side="left")
            
            label_message = tk.Label(message_frame, text=message, font=("Arial", 15), bg="white", bd=0,anchor="w")       
            label_message.pack(side="left")
            
            # Tự động cuộn xuống cuối
            root.after(20, lambda: canvas.yview_moveto(1.0))
            
            # Xóa nội dung trong entry sau khi gửi tin nhắn
            entry.delete(0, tk.END)

            command, path, warn = normalize_input(message)
            if (warn != ""):
                warn_label_frame=tk.Frame(scrollable_frame, bg="white")
                warn_label_frame.pack(side="top", fill="x", pady=(0, 3))
                warn_label=tk.Label(warn_label_frame, text=warn, font=("Arial", 15), bg="lightyellow", fg="crimson", anchor="w")
                warn_label.pack(side="left", padx=5)
            else:
                if command.strip().lower()=='upload':
                    
                    isUploaded = False
                    if os.path.isfile(path):
                        send_message(message)
                        isUploaded = upload_file(path)
                    else:
                        send_message(f"upload_folder {path}")
                        isUploaded = upload_folder(path)

                    #Nếu isUploaded = True nghĩa là upload thành công, thì in ra phản hồi của Server lên message_frame. 
                    if isUploaded:
                        label_frame=tk.Frame(scrollable_frame, bg="white")
                        label_frame.pack(side="top", fill="x", pady=(0, 3))
                        label = tk.Label(label_frame, text='File has been uploaded', font=("Tahoma", 15), bg="lightgreen", fg="navy", anchor="w")
                        label.pack(side="left", padx=5)
                    else:
                        label_frame=tk.Frame(scrollable_frame, bg="white")
                        label_frame.pack(side="top", fill="x", pady=(0, 3))
                        label = tk.Label(label_frame, text='Fail to upload this file', font=("Tahoma", 15), bg="red", anchor="w")
                        label.pack(side="left",padx=5)
                if command.strip().lower()=='download':
                    send_message(message)
                    isDownloaded = receive_file(path)
                    #Nếu isUploaded = True nghĩa là upload thành công, thì in ra phản hồi của Server lên message_frame. 
                    if isDownloaded:
                        label_frame=tk.Frame(scrollable_frame, bg="white")
                        label_frame.pack(side="top", fill="x", pady=(0, 3))
                        label = tk.Label(label_frame, text='File has been downloaded', font=("Tahoma", 15), bg="lightgreen", fg="navy", anchor="w")
                        label.pack(side="left", padx=5)
                    else:
                        label_frame=tk.Frame(scrollable_frame, bg="white")
                        label_frame.pack(side="top", fill="x", pady=(0, 3))
                        label = tk.Label(label_frame, text='Fail to download this file', font=("Tahoma", 15), bg="red", anchor="w")
                        label.pack(side="left",padx=5)
                
    server_label = tk.Label(root, text=f"{username} [{localIP}, {localPORT}]", font=("Arial", 15, "bold"),  bg="green", fg="yellow")
    server_label.pack(padx=30, pady=10, side="top", anchor="w")
    main_frame = tk.Frame(root, borderwidth=2, relief="solid")
    main_frame.pack(padx=20, pady=(5, 10), fill="both", expand=True)

    # Tạo canvas và scrollbar cho vùng tin nhắn
    canvas = tk.Canvas(main_frame, bg="white")
    vertical_scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    horizontal_scrollbar = tk.Scrollbar(main_frame, orient="horizontal", command=canvas.xview)
    scrollable_frame = tk.Frame(canvas, bg="white")

    # Liên kết canvas với scrollbar
    canvas.configure(yscrollcommand=vertical_scrollbar.set, xscrollcommand=horizontal_scrollbar.set)

    vertical_scrollbar.pack(side="right", fill="y")
    horizontal_scrollbar.pack(side="bottom", fill="x")
    canvas.pack(side="left", fill="both", expand=True)
    canvas.create_window((0, 0), window=scrollable_frame, anchor="center")

    # Cập nhật vùng cuộn khi nội dung thay đổi
    scrollable_frame.bind("<Configure>",lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    # Liên kết sự kiện cuộn chuột với canvas
    canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(-1 * (event.delta // 120), "units"))  # Cuộn trên Windows
    
    # Vùng nhập tin nhắn và gửi
    entry_frame = tk.Frame(root)
    entry_frame.pack(side="top", anchor='w', fill="x", pady = 5)

    # Nút thứ nhất (Góc trái)
    upload_button = tk.Button(entry_frame, text="Upload", font=("Arial", 13), command = choose_upload)
    upload_button.pack(side="left", padx=(10, 5))  # Cách lề trái 10px, cách nút thứ hai 5px

    # Nút thứ hai (Kế bên nút 1)
    download_button = tk.Button(entry_frame, text="Download", font=("Arial", 13),command = show_list_file)
    download_button.pack(side="left", padx=(0, 10))  # Cách nút 1 không gian 0px, cách khung nhập 10px

    entry = tk.Entry(entry_frame, font=("Arial", 15))
    entry.pack(side="left", fill="x", expand=True, padx=(10, 0))
    entry.bind("<Return>", ib_message)  # Gửi tin nhắn khi nhấn Enter
    entry.focus()

    send_button = tk.Button(entry_frame, text="Send", font=("Arial", 13), command=ib_message)
    send_button.pack(side="left", padx=(7,10))


def menu_login():
    for widget in root.winfo_children():
        widget.destroy()

    root.title("Login")
    root.geometry("700x500")  # Tăng kích thước cửa sổ chính
    #root.attributes("-topmost", True)

    # Tạo một khung lớn hơn
    main_frame = tk.Frame(root, bg="lightblue", borderwidth=2, relief="flat")
    main_frame.pack(padx=50, pady=50, fill="both", expand=True)

    # Thêm tiêu đề
    label = tk.Label(main_frame, text="Sign in", font=("Arial", 30, "bold"), bg="lightblue")
    label.pack(side="top", anchor="center", pady=10)

    # Ô nhập tên đăng nhập
    user_frame = tk.Frame(main_frame, bg="lightblue")
    user_frame.pack(side="top", anchor="center", pady=10)
    user_label = tk.Label(user_frame, text="Username:", bg="lightblue", font=("Arial", 15))
    user_label.pack(side="left")
    user_entry = tk.Entry(user_frame, font=("Arial", 12), width=25)
    user_entry.insert(0, "Username")
    user_entry.pack(side="left", padx=5)

    def user_focus_in(e):
        if user_entry.get() == "Username":
            user_entry.delete(0, tk.END)
    def user_focus_out(e):
        if user_entry.get() == "":
            user_entry.insert(0, "Username")
    
    user_entry.bind("<FocusIn>", user_focus_in)
    user_entry.bind("<FocusOut>", user_focus_out)

    # Ô nhập mật khẩu
    pass_frame = tk.Frame(main_frame, bg="lightblue")
    pass_frame.pack(side="top", anchor="center", pady=10)
    pass_label = tk.Label(pass_frame, text="Password:", bg="lightblue", font=("Arial", 15))
    pass_label.pack(side="left")
    pass_entry = tk.Entry(pass_frame, font=("Arial", 12), width=25)
    pass_entry.insert(0, "Password")
    pass_entry.pack(side="left", padx=5)

    def pass_focus_in(e):
        if pass_entry.get() == "Password":
            pass_entry.delete(0, tk.END)
            pass_entry.config(show="*")
    def pass_focus_out(e):
        if pass_entry.get() == "":
            pass_entry.insert(0, "Password")
            pass_entry.config(show="")
    
    pass_entry.bind("<FocusIn>", pass_focus_in)
    pass_entry.bind("<FocusOut>", pass_focus_out)

    user_entry.focus()

    def click_reset():
        print(" ")

    # Ô đặt lại mật khẩu
    reset_button = tk.Button(main_frame, text="Reset password", font=("Arial", 12, "bold"), bg="lightblue", fg = "purple", command=click_reset)
    reset_button.pack(pady=15)

    check_click_login=False
    def click_Login(event=None):
        nonlocal check_click_login
        if check_click_login:
            return
        check_click_login=True

        username = user_entry.get()
        password = pass_entry.get()

        isLogined, username = client_login(username, password)
        if isLogined:
            success_label = tk.Label(main_frame, text=f"Login successful! Welcome, {username}", font=("Arial", 17, "bold"), bg="yellow", fg = "red")
            success_label.pack(pady=15)
            root.after(2000, lambda: main(username))
        else:
            fail_label = tk.Label(main_frame, text="Login failed! Invalid username or password.", font=("Arial", 17, "bold"), bg="yellow", fg = "red")
            fail_label.pack(pady=15)
            root.after(2000, lambda: fail_label.destroy())

        def reset_login_flag():
            nonlocal check_click_login
            check_click_login = False
        root.after(2000, reset_login_flag)

    # Nút đăng nhập
    login_button = tk.Button(main_frame, text="Login", bg="lightgreen", font=("Arial", 15, "bold"), command=click_Login)
    login_button.pack(pady=15)

    user_entry.bind("<Return>", click_Login)
    pass_entry.bind("<Return>", click_Login)

menu_login()
root.mainloop()