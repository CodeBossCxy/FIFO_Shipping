var container_to_scan = [];
var building_code = "";
var adminMode = false;
const ADMIN_PASSCODE = "vintech2026";

function verifyPasscode() {
    const input = document.getElementById('admin-passcode');
    const error = document.getElementById('admin-error');
    const btn = document.getElementById('admin-btn');
    const modal = document.getElementById('admin-modal');
    const title = document.getElementById('admin-modal-title');

    if (adminMode) {
        // Turning off admin mode
        adminMode = false;
        btn.classList.remove('active');
        btn.textContent = 'Admin';
        modal.style.display = 'none';
        input.value = '';
        error.style.display = 'none';
        show_popup("Admin mode deactivated", true);
        return;
    }

    if (input.value === ADMIN_PASSCODE) {
        adminMode = true;
        btn.classList.add('active');
        btn.textContent = 'Admin';
        modal.style.display = 'none';
        input.value = '';
        error.style.display = 'none';
        show_popup("Admin mode activated - FIFO override enabled", true);
    } else {
        error.style.display = 'block';
    }
}

document.getElementById('admin-btn').addEventListener('click', function() {
    if (adminMode) {
        // If already in admin mode, toggle off directly
        adminMode = false;
        this.classList.remove('active');
        this.textContent = 'Admin';
        show_popup("Admin mode deactivated", true);
    } else {
        document.getElementById('admin-modal').style.display = 'flex';
        document.getElementById('admin-error').style.display = 'none';
        document.getElementById('admin-passcode').value = '';
        document.getElementById('admin-passcode').focus();
    }
});

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
                    container_to_scan.push(container.Serial_No);
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

async function get_master_containers(master_unit_no) {
    console.log("[get_master_containers] master_unit_no: ", master_unit_no);
    return await fetch(`/check/master_containers`,
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                master_unit_no: master_unit_no
            })
        }
    ).then(response => response.json()).then(data => {
        console.log("data: \n", data);
        return data;
    //     
    })
    .catch(error => {
        console.error('Error updating serial no:', error);
    });



    // const myHeaders = new Headers();
    // myHeaders.append("Authorization", "Basic VmludGVjaFdTQHBsZXguY29tOmE0Y2Q3OGEtZmUxMi00");
    // myHeaders.append("Content-Type", "application/json");

    // const raw = JSON.stringify({
    //     "inputs": {
    //     "Master_Unit_No": master_unit_no
    //     }
    // });

    // const requestOptions = {
    //     method: "POST",
    //     headers: myHeaders,
    //     body: raw,
    //     redirect: "follow"
    // };
    // try {
    //     result = await fetch("https://Vintech.on.plex.com/api/datasources/12934/execute", requestOptions)
    //     if (!result.ok) {
    //         throw new Error('Network response was not ok');
    //     }
    //     const data = await result.json();
    //     console.log("data: ", data);
    //     return data;
    // } catch (error) {
    //     console.error('Error getting master unit:', error);
    // }
    

    // return result;
}


async function update_master_unit(master_unit_no) {
    fetch(`/update/master_unit`,
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                master_unit_no: master_unit_no,
                building_code: building_code
            })
        }
    ).then(response => response.json()).then(data => {
        console.log("data: \n", data);
    })  
    .catch(error => {
        console.error('Error updating master unit:', error);
    });
}

async function send_scanner_input() {
    scanner_input.addEventListener('input', async () => {
        clearTimeout(scanTimeout);
        scanBuffer = scanner_input.value;
        scanTimeout = setTimeout(async () => {
            console.log("scanBuffer: ", scanBuffer);
            if (scanBuffer[0] == "M"){
                try {
                    const container_list = await get_master_containers(scanBuffer)
                    console.log("container_list: ", container_list.containers);
                    const invalidContainers = container_list.containers.filter(container => !container_to_scan.find(serial => container.includes(serial)));
                    if (invalidContainers.length === 0) {
                        update_master_unit(scanBuffer);
                        show_popup("Master unit scanned successfully", true);
                    } else if (adminMode) {
                        update_master_unit(scanBuffer);
                        show_popup("Admin override: master unit scanned", true);
                    } else {
                        show_popup("FIFO violation: " + invalidContainers.join(", "), false);
                    }
                } catch (error) {
                    console.error('Error getting master unit:', error);
                }
            }
            else if (container_to_scan.find(serial => scanBuffer.includes(serial))) {
                const matched_serial = container_to_scan.find(serial => scanBuffer.includes(serial));
                console.log("available container scanned: ", matched_serial);
                update_serial_no(matched_serial);

            } else if (adminMode) {
                console.log("Admin override - scanning: ", scanBuffer);
                update_serial_no(scanner_input.value);
                show_popup("Admin override: container scanned", true);
            } else {
                show_popup("Invalid container, violating FIFO policy", false);
            }
        }, 1000);
    });
}

let scanBuffer = '';
let scanTimeout;
const scanner_input = document.getElementById('scanner-input');

load_shipper_containers();
send_scanner_input();

// Set focus to the scanner input field when page loads
document.addEventListener('DOMContentLoaded', function() {
    if (scanner_input) {
        scanner_input.focus();
    }
});
