var container_to_scan = [];
var building_code = "";
async function load_shipper_containers() {
    console.log("Successfully loaded");
    const shipper_number = document.querySelector('h1').textContent;
    console.log("shipper_number: ", shipper_number);
    fetch(`/shipper/${shipper_number}`,
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        }
    ).then(response => response.json()).then(data => {
        const containers = document.getElementById('shipper-table-container');
        console.log("data: \n", data);
        // console.log(typeof data);
        let table = '<table style="width: 100%;" display="block">';
        table += '<thead><tr><th>Serial No</th><th>Quantity</th><th>Location</th></tr></thead>';
        table += '<tbody>';
        console.log("data.dataframes: \n", data.dataframes);
        data.dataframes.forEach((part, index) => {
            console.log(`-- part ${index + 1} --`);
            console.log(part[0].Status);
            building_code = part[0].Building_Code;
            if (part[0].Status == "Containers Available") {
                table += `<tr style="background-color: #e0e0e0; font-weight: bold; "><td colspan="3">${part[0].Part_No}: </td></tr>`;
                part.forEach(container => {
                    container_to_scan += container.Serial_No;
                    table += `<tr><td>${container.Serial_No}</td><td>${container.Quantity}</td><td>${container.Location}</td></tr>`;
                });
                // table += <tr style="height: 20px;"><td></td></tr> 
            } else if (part[0].Status == "No Containers Available") {
                table += `<tr style="background-color: #e0e0e0; font-weight: bold;"><td colspan="2">${part[0].Part_No}</td><td colspan="1">No Containers Available</td></tr>`;
                // table += <tr style="height: 20px;"><td></td></tr> 
            } else if (part[0].Status == "Load Complete") {
                table += `<tr style="background-color: #e0e0e0; font-weight: bold;"><td colspan="2">${part[0].Part_No}</td><td colspan="1">Part Loaded</td></tr>`;
                // table += <tr style="height: 20px;"><td></td></tr> 
            }
        })
        table += '</tbody></table>';
        console.log("table: \n", table);
        containers.innerHTML = table;
    })
    .catch(error => {
        console.error('Error fetching shipper data:', error);
    });
}


function update_serial_no(serial_no) {
    console.log("[update_serial_no] serial_no: ", serial_no);
    const shipper_number = document.querySelector('h1').textContent;
    fetch(`/shipper/scan/${serial_no}`,
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                serial_no: serial_no,
                shipper_number: shipper_number,
                building_code: building_code
            })
        }
    ).then(response => response.json()).then(data => {
        console.log("data: \n", data);
        if(data.message == "Success") {
            show_popup("Container scanned successfully", true);
        } else {
            show_popup("Issue, please check", false);
        }
    })
    .catch(error => {
        console.error('Error updating serial no:', error);
    });
}


function show_popup(message, sucess = true) {
    const popup = document.getElementById('popup');
    popup.innerText = message;
    popup.style.display = 'block';
    const audio = sucess ? document.getElementById('success-sound') : document.getElementById('error-sound');

    if (sucess) {
        popup.style.backgroundColor = 'green';
    } else {
        popup.style.backgroundColor = 'red';
    }
    audio.currentTime = 0;
    audio.play();
    setTimeout(() => {
        popup.style.display = 'none';
        scanner_input.value = '';
        scanner_input.focus();
    }, 3000);
}

function simulateScan(value) {
    scanner_input.value = value;
    scanner_input.dispatchEvent(new Event('input'));
}
// simulateScan("ABC12345");  // Call this in console to simulate a scan


function send_scanner_input() {
    
    scanner_input.addEventListener('input', () => {
        clearTimeout(scanTimeout);
        scanBuffer = scanner_input.value;
        scanTimeout = setTimeout(() => {
            console.log("scanBuffer: ", scanBuffer);
            if (container_to_scan.includes(scanBuffer)) {
                console.log("available container scanned: ",scanBuffer);
                update_serial_no(scanner_input.value);
                
            } else {
                alert("Invalid container, violating FIFO policy");
            }
        }, 1000);
        // if (event.key === "Enter") {
        //     event.preventDefault();
        //     console.log("scanner_input: ", scanner_input.value);
        // if (container_to_scan.includes(scanner_input.value)) {
        //     console.log("available container scanned: ",scanner_input.value);
        //     update_serial_no(scanner_input.value);
        // } else { 
        //     alert("Invalid container, violating FIFO policy");
        // } 
    });
}

let scanBuffer = '';
let scanTimeout;
const scanner_input = document.getElementById('scanner-input');

load_shipper_containers();
send_scanner_input();
