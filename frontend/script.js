async function load_shipper(){
    console.log("Successfully loaded");
    fetch('/api/get_valid_shippers',
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        }
    ).then(response => response.json()).then(data => {
        const container = document.getElementById('shipper-table-container');
        let table = '<table>';
        table += '<thead><tr><th>Shipper No</th><th>Customer Code</th></tr></thead>';
        table += '<tbody>';
        data.forEach(shipper => {
            table += `<tr><td>${shipper.Shipper_No}</td><td>${shipper.Customer_Code}</td></tr>`;
        });
        table += '</tbody></table>';
        container.innerHTML = table;
    })
    .catch(error => {
        console.error('Error fetching shipper data:', error);
    });
}

load_shipper();