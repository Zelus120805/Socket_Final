import socket
import threading
import os
import datetime
import logging

HEADER = 4096
FORMAT = 'utf-8'
IP = socket.gethostbyname(socket.gethostname())
PORT = 65432
#Chỉ định giao thức TCP

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#Gắn socket với địa chỉ addr(IP,portNumber)

ADDR = (IP, PORT) #Định nghĩa một tuple địa chỉ
server.bind(ADDR) #Kết nối socket với địa chỉ.

now = datetime.datetime.now()
FILENAME_HISTORY = f"{now.strftime('%d-%m-%Y  %H_%M_%S')}.txt"
FILE_PATH_HISTORY = os.path.join(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"HISTORY"), FILENAME_HISTORY)
def setup_logger(file_path):
    logging.basicConfig(
        filename=file_path,
        level=logging.INFO,  # Ghi các thông tin từ mức INFO trở lên
        format='%(asctime)s - %(message)s',  # Định dạng log
        datefmt='[%d/%m/%Y %H:%M:%S]',  # Định dạng thời gian
        encoding='utf-8'  # Hỗ trợ UTF-8
    )
setup_logger(FILE_PATH_HISTORY)

#==================================================================================
#Tổ chức cấu trúc cây để phân cấp thư mục. 
class Node:
    def __init__(self, fileName, size, dateModified,path):
        self.name = fileName
        self.size = size
        self.dateModified = dateModified
        self.path = path
        self.children = []
    def add_child(self, newNode):
        self.children.append(newNode)

def send_message(conn, msg):
    msgContent = msg.encode(FORMAT)
    msgLength = len(msgContent)
    sendLength = str(msgLength).encode(FORMAT)
    sendLength += b' '*(HEADER - len(sendLength))
    conn.send(sendLength)
    conn.send(msgContent)
    
def receive_message(conn):
    msgLength = int(conn.recv(HEADER).decode(FORMAT))
    msgContent = conn.recv(msgLength).decode(FORMAT)
    return msgContent

def read_file_user():
    def get_current_dirname(fileName):
        baseDir = os.path.dirname(os.path.abspath(__file__))
        # Tạo đường dẫn tới file  trong thư mục Demo_Server
        filePath = os.path.join(baseDir, fileName)
        # Mở file
        return filePath

    fileUsers = open(get_current_dirname('Users.txt'),"r")
    listUsers = {}
    for line in fileUsers:
        n,p = line.strip().split(",")
        listUsers[n.strip()] = p.strip()
    fileUsers.close()
    return listUsers
listUsers = read_file_user()

def client_login(conn):
    #Nhận tên đăng nhập 
    userName = receive_message(conn)
   
    #Nhận mật khẩu
    password = receive_message(conn)
    
    #Kiếm tra tên đăng nhập
    if userName in listUsers:
        if listUsers[userName] == password:
            conn.send(str(1).encode(FORMAT)) #Gửi phản hồi đăng nhập đúng
            logging.info(f"[LOGIN SUCCESSFULLY] {userName}")
            return True, userName
        else:
            conn.send(str(0).encode(FORMAT)) #Gửi phản hồi đăng nhập sai. 
            return False, userName
    return False, userName

def main(conn, addr, userName, isLogined):
    def normalize_input(request):
    #Loại bỏ kí tự, khoảng trắng thừa đầu, cuối
        request.strip()
        
        #Tách thành 2 phần (Hoặc 1 phần)
        parts = request.split(maxsplit = 1)
        command = ""
        filePath = ""

        if len(parts) < 2:
                command=parts[0]
        else:
            command = parts[0]
            filePath = parts[1]
            #Chuẩn hóa đường dẫn
            filePath.strip()
            if filePath.startswith('"') and filePath.endswith('"'):
                filePath = filePath[1:-1]
            if not os.path.exists(filePath) and command == 'upload':
                print("Your path isn't exists")

        return command, filePath

    def receive_file_from_client(conn, filePath):
        saveDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"DOWNLOADS\\{userName}")
        if not os.path.exists(saveDir):
            os.mkdir(saveDir)

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
        
        fileName = os.path.basename(filePath)
        fileName = handle_duplicate_file_name(fileName,saveDir) #Xử lí file trùng

        savePath = os.path.join(saveDir, fileName)
        fout = open(savePath, "wb") #Tạo một file mới để ghi dữ liệu vào, mở chế độ nhị phân

        try:
            while True:
                # Tin nhắn đầu tiên là độ dài của nội dung mà server có thể nhận
                fileLength = conn.recv(HEADER).decode(FORMAT)
                
                if not fileLength:
                    break  # Nếu fileLength rỗng, thoát vòng lặp
                fileLength = int(fileLength) #Chuyển kích thước dạng chuỗi về dạng số nguyên
                
                if fileLength == 0: #Đến khi hết dữ liệu thì không ghi nữa, thoát vòng lặp 
                    break
                
                data = conn.recv(fileLength)
                
                if not data:    
                    break  # Nếu không có dữ liệu, thoát vòng lặp
                fout.write(data)  # Ghi dữ liệu vào file
        except Exception as e:
            #print(f"Error receiving file: {e}")
            logging.error("File received unsuccessfully.")
            conn.send("Uploaded unsuccessfully!".encode(FORMAT))
            fout.close()
            return
            
        logging.info("File received successfully.")
        # Gửi phản hồi về client sau khi hoàn tất
        conn.send("Uploaded successfully!".encode(FORMAT))    
        fout.close()

    def receive_folder_from_client(conn, base_dir):
        try:
            os.makedirs(base_dir, exist_ok=True)  # Đảm bảo thư mục DOWNLOADS tồn tại

            root_folder_name = receive_message(conn)  # Nhận tên thư mục gốc
            root_folder_path = os.path.join(base_dir, root_folder_name)
            os.makedirs(root_folder_path, exist_ok=True)  # Tạo thư mục gốc

            while True:
                # Nhận đường dẫn tương đối
                relative_path = receive_message(conn)
                if relative_path == "END":  # Nếu nhận tín hiệu kết thúc
                    break

                # Xây dựng đường dẫn đầy đủ
                full_path = os.path.join(root_folder_path, relative_path)
   
                # Kiểm tra xem là file hay folder
                item_type = receive_message(conn)
                if item_type == "FOLDER":
                    os.makedirs(full_path, exist_ok=True)  # Tạo thư mục
                elif item_type == "FILE":
                    # Nhận file và lưu vào đường dẫn tương ứng
                    with open(full_path, "wb") as f:
                        while True:
                            file_size = int(conn.recv(HEADER).decode(FORMAT).strip())
                            if file_size == 0:  # Tín hiệu kết thúc file
                                break
                            data = conn.recv(file_size)
                            f.write(data)

            logging.info("Folder received successfully.")
        except Exception as e:
            #print(f"Error receiving folder: {e}")
            logging.error("Folder received unsuccessfully.")

    downloads = {}
    def send_file_to_client(socketClient, fileName):
        filePath = downloads[fileName]
        #print(filePath)
        try:
            fin = open(filePath, "rb")
        except:
            #Gửi tín hiệu file không đọc được
            logging.info("file sended unsuccessfully.")
            send_message(socketClient,'-1')
            return
        #Tín hiệu file đã đọc được
        logging.info("file sended successfully.")
        send_message(socketClient, '1')
        sizeOfFile = os.path.getsize(filePath)  # Lấy kích thước file
        #print(f"Size: {sizeOfFile}")
        send_message(socketClient,str(sizeOfFile))
        totalBytes = 0  # Tính toán tổng số bytes đã tải

        while totalBytes < sizeOfFile:
            stop_sending = receive_message(socketClient)
            if stop_sending == '0':
                break
            #Đọc một lần tối thiểu 1024b
            data = fin.read(HEADER)
            if not data:
                break;
            finLength = len(data)
            sendLength = str(finLength).encode()
            sendLength += b' '*(HEADER- len(sendLength))
            socketClient.send(sendLength)
            socketClient.send(data)
            totalBytes += len(data)

        fin.close()
        
    def get_info(filePath):
        #Lấy kích thước file
        sizeOfFile = os.path.getsize(filePath)
        #Lấy thời gian (time modified)
        timeStamp = os.path.getmtime(filePath)
        dateModified = datetime.datetime.fromtimestamp(timeStamp).date()
        return sizeOfFile, dateModified

    def traversal_folder(folderPath, root):
        #Liệt kê tất cả file và thư mục con trong thư mục tại root
        listItem = os.listdir(folderPath)
        #Duyệt từng file và thư mục con trong danh sách
        for item in listItem:
            #Lấy đường dẫn 
            itemPath = os.path.join(folderPath,item)
            #Lấy kích thước và date modified
            size, date = get_info(itemPath)
            #Tạo một node mới và thêm vào con của thư mục hiện tại
            newNode = Node(item, size, date, itemPath)
            downloads[newNode.name] = newNode.path
            root.add_child(newNode)
            #Nếu đó node đó là thư mục, duyệt tiếp thư mục con đó.
            if os.path.isdir(itemPath):
                traversal_folder(itemPath, newNode)
            #Còn nếu node đó là file, không làm gì vì nó đã là node lá rồi. 
    
    def send_list_file_to_client_v2(socketClient, addrClient):
        
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        currentDir = os.getcwd()
        currentDir = os.path.join(currentDir,"DOWNLOADS")
        items = os.listdir(currentDir)
        #Khởi tạo cây thư mục với root là thư mục DOWNLOADS
        root = Node('',0,'','')
        root.name = 'DOWNLOADS'
        root.size, root.dateModified = get_info(currentDir)
        root.path = currentDir
        #Duyệt tất cả các phần tử trong thư mục DOWNLOADS
        for name in items:
            #Lấy đường dẫn của phần tử đó
            itemPath = os.path.join(currentDir, name)
            if os.path.isdir(itemPath):
                #Lấy các thông tin và thêm vào cây
                size, date = get_info(itemPath)
                newNode = Node(name, size, date, itemPath)
                root.add_child(newNode)
                #Thêm vào dictionary với key là newNode.name
                downloads[newNode.name] = newNode.path
                #Gọi đệ quy để thêm tiếp các thư mục con nếu có. 
                traversal_folder(itemPath,newNode)
        #Gửi thông tin cho client.
        send_preOrder(socketClient, root)
        
    def send_preOrder(socketClient, root):
        if not root:
            return
        #Gửi số con của node đó, báo hiệu rằng n node tiếp theo phải nhận là con của nó.
        send_message(socketClient,str(len(root.children))) 
        #Gửi tên
        send_message(socketClient,root.name) 
        #Gửi kích thước
        send_message(socketClient,str(root.size))
        #Gửi ngày sửa đổi
        send_message(socketClient,str(root.dateModified))
        #Duyệt qua các con của nó và tiếp tục gửi theo tiền thứ tự.
    #  print((len(root.children),root.name,root.size,root.dateModified))
        for child in root.children:
            send_preOrder(socketClient, child)

    def preOrder(root,level):
        if not root:
            return

        # Thụt đầu dòng theo cấp độ
        indent = "  " * level
        print(f"{indent}- {root.name} (Size: {root.size}, Modified: {root.dateModified}) - Level {level}")

        # Duyệt qua các nút con
        for child in root.children :
            preOrder(child,level + 1)
    
    try: 
        while True:
            requestContent = receive_message(conn)
            logging.info(f"[Client - {userName}] {requestContent}")
            command = ""
            filePath = ""
            command, filePath = normalize_input(requestContent)
            
            if command.strip().lower() == 'close':
                conn.close()
                return False
            
            if command.strip().lower() == 'logout':
                logging.info(f"[LOGOUT SUCCESSFULLY] {userName}")
                isLogined = False
                return isLogined
            elif command.strip().lower() == 'upload' and filePath:
                receive_file_from_client(conn, filePath)
            elif command.strip().lower() == 'upload_folder':
                download_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"DOWNLOADS\\{userName}")
                receive_folder_from_client(conn, download_dir)
            elif command.strip().lower()=='view':
                send_list_file_to_client_v2(conn,addr)
            elif command.strip().lower()=='download':
                send_file_to_client(conn,filePath)
    except: 
        conn.close()
        return
    
def handle_client(conn, addr):
    logging.info(f"[ACTIVE CONNECTION] {threading.active_count() - 1}")
    logging.info(f"[NEW CONNECTION] {addr} connected.")
    #Code đăng nhập ------------------------------------------------------------------
    isLogined = False
    userName = ""
    while not isLogined:
        try:
            isLogined, userName = client_login(conn)
        except:
            conn.close()
            logging.info(f"Disconnected from {addr}")
            return
    #---------------------------------------------------------------------------------
        while isLogined:
            isLogined = main(conn, addr, userName, isLogined)

def start_server():
    #Lắng nghe chờ đợi kết nối
    server.listen()
    logging.info(f"[STARTING] Server is listening on {ADDR}")
    
    #Khi client tới
    while True:
        #Lấy địa chỉ client và tạo một socket riêng, dành cho việc trao đổi với client này
        newClient, newADDR = server.accept()
        
        #Tạo luồng xử lí cho client này
        newThread = threading.Thread(target = handle_client, args = (newClient,newADDR), daemon = True)
        
        #Bắt đầu luồng xử lí này.
        newThread.start()

start_server()