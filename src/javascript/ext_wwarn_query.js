// Need this class to be able to download directly from an Ext component
Ext.ux.Report = Ext.extend(Ext.Component, {
    autoEl: {tag: 'iframe', cls: 'x-hidden', src: Ext.SSL_SECURE_URL},
    load: function(config){
        this.getEl().dom.src = config.url + (config.params ? '?' + Ext.urlEncode(config.params) : '');
    }
});
Ext.reg('ux.report', Ext.ux.Report);


// Clears out all the values in the input text fields and checkboxes found
// on the WWARN db query form
function clearWWARNQueryForm() {
    Ext.getCmp('wwarnFormPanel').getForm().reset();
}

// If given the checked values from an Ext CheckBoxGroup
// we should return the values of said check boxes in an
// array
function getValuesFromCheckBoxGroup(checkBoxGroupObj) {
	var checkboxGroupValueArray = new Array();
	
	for (var i = 0; i < checkBoxGroupObj.length; i++) {
        if ( checkBoxGroupObj[i].getRawValue() != "" ) {
    		checkboxGroupValueArray.push( checkBoxGroupObj[i].getRawValue() );
        }
	}
	
	return checkboxGroupValueArray;
}

// Queries the WWARN database via CGI script
function queryWWARNDB() {

	// We need to grab the contents of the fields and combo-boxes in the HTML form 
	// found on the page
	var investigatorName = document.getElementById('text_investigator').value;
	var studyCountry = document.getElementById('text_studycountry').value;
	var studySite = document.getElementById('text_studysite').value;
	var studyGroup = document.getElementById('text_studygroup').value;
	var locusName = document.getElementById('text_locusname').value;
	var locusPos = document.getElementById('text_locuspos').value;
	var age = document.getElementById('text_age').value;
	var sampleDate = document.getElementById('text_collectiondate').value;
	var inclusionDate = document.getElementById('text_inclusiondate').value;
    var markerValue = document.getElementById('text_markervalue').value;
	var markerTypeArray = getValuesFromCheckBoxGroup(Ext.getCmp('checkboxgroup_markertype').getValue());
	var mutantStatusArray = getValuesFromCheckBoxGroup(Ext.getCmp('checkboxgroup_mutantstatus').getValue());

    var grid = Ext.getCmp('wwarnDBGrid');
    var store = grid.getStore();

    // Unmask the grid and pagingToolbar
    grid.el.unmask();
    grid.getGridEl().unmask();
    grid.getBottomToolbar().getEl().unmask();

    // We need to reset our base parameters in order for our 
    // reload of data to carry over to our PagingToolbar
    store.removeAll();
    store.setBaseParam('investigator', investigatorName);
    store.setBaseParam('study_group', studyGroup);
    store.setBaseParam('site', studySite);
    store.setBaseParam('age', age);
    store.setBaseParam('sample_date', sampleDate);
    store.setBaseParam('inclusion_date', inclusionDate);
    store.setBaseParam('country', studyCountry);
    store.setBaseParam('loc_name', locusName);
    store.setBaseParam('loc_pos', locusPos);
    store.setBaseParam('marker_type', markerTypeArray);
    store.setBaseParam('genotype_mut_stat', mutantStatusArray);
    store.setBaseParam('marker_value', markerValue);
    store.setBaseParam('download', '');
    store.load({ start: 0, limit: 25 });
 
    grid.render();
}

Ext.onReady(function(){
    Ext.QuickTips.init();

    // Form we will be using to query results
    var dbForm = new Ext.FormPanel({
        id: 'wwarnFormPanel',
        labelWidth: 100,
        bodystyle: 'padding: 5px 5px 0',
        style: 'margin: 0 0 0 5px',
        frame: true,
        width: 730,

        items: [{
            xtype: 'fieldset',  
            title: 'Standard Parameters',
            autoHeight: true,
            items: [{
                layout: 'column',
                border: false,
                items: [{
                    columnWidth: .5,
                    layout: 'form',
                    border: false,
                    defaults: {
                        width: 210,
                        style: 'margin: 0 0 6px 0',
                        msgTarget: 'side'
                    },
                    defaultType: 'textfield',
                    items: [{
                        id: 'text_studylabel',
                        fieldLabel: 'Study Label',
                        allowBlank: true,
                    },{
                        id: 'text_studycountry',
                        fieldLabel: 'Country',
                        allowBlank: true,
                    },{
                        id: 'text_studysite',
                        fieldLabel: 'Site',
                        allowBlank: true,
                    },{
                        xtype: 'checkboxgroup',
                        id: 'checkboxgroup_mutantstatus',
                        fieldLabel: 'Mutant Status',
                        columns: 2,
                        items: [
                                    {boxLabel: 'Mutant', inputValue: 'Mutant', name: 'cb-status-mutant'},
                                    {boxLabel: 'Wild', inputValue: 'Wild', name: 'cb-status-wild'},
                                    {boxLabel: 'Mixed', inputValue: 'Mixed', name: 'cb-status-mixed'},
                                    {boxLabel: 'No data', inputValue: 'No data', name: 'cb-status-nodata'}  
                        ]
                    }]
                },{
                    columnWidth: .5,
                    layout: 'form',
                    border: false,
                    defaults: {
                        width: 210,
                        style: 'margin: 0 0 6px 0',
                        msgTarget: 'side'
                    },
                    defaultType: 'textfield',
                    items: [{
                        id: 'text_locusname',
                        fieldLabel: 'Locus Name',
                        allowBlank: true,
                    },{
                        id: 'text_locuspos',
                        fieldLabel: 'Locus Position',
                        allowBlank: true,
                    },{
                        id: 'text_investigator',
                        fieldLabel: 'Investigator',
                        allowBlank: true,
                    },{
                        xtype: 'checkboxgroup',
                        id: 'checkboxgroup_markertype',
                        fieldLabel: 'Marker Type',
                        columns: 1,
                        items: [
                                    {boxLabel: 'SNP', inputValue: 'SNP', name: 'cb-type-snp'},
                                    {boxLabel: 'Copy Number', inputValue: 'Copy Number', name: 'cb-type-cn'},
                                    {boxLabel: 'Fragment', inputValue: 'Fragment', name: 'cb-type-frag'}
                        ]
                    }]
                }]
            }]
        },{
            xtype: 'fieldset',  
            title: 'Advanced Parameters',
            autoHeight: true,
            defaults: {
                width: 210,
                style: 'margin: 0 0 6px 0'
            },
            defaultType: 'textfield',
            collapsed: false,
            items: [{
                id: 'text_studygroup',
                fieldLabel: 'Study Group',
                allowBlank: true,
            },{
                id: 'text_inclusiondate',
                fieldLabel: 'Date of Inclusion',
                allowBlank: true,
            },{
                id: 'text_collectiondate',
                fieldLabel: 'Collection Date',
            },{
                id: 'text_age',
                fieldLabel: 'Age'
            },{
                id: 'text_markervalue',
                fieldLabel: 'Marker Value'
            }]
        },{
            buttons: [{
                text: 'Submit',
                handler: function() {
                    queryWWARNDB();
                }
            },{
                text: 'Clear',
                handler: function() {
                    clearWWARNQueryForm();
                }
            }]
                
        }]
    });

	dbForm.render('wwarndb_query_form');
	dbForm.show();
	
    var wwarnHTTPProxy = new Ext.data.HttpProxy({
        url: '/cgi-bin/wwarn/wwarn_db_query.cgi',
        method: 'GET'
    });

    var wwarnDBStore = new Ext.data.Store({
		id: 'wwarnDBStore',
		proxy: wwarnHTTPProxy,
        baseParams: {},
	    reader: new Ext.data.JsonReader({
		root: 'results',
		totalProperty: 'total',
		id: 'id',
	},[
	   {name: 'study_label', type: 'string', mapping: 'study_label'},
	   {name: 'study_group', type: 'string', mapping: 'study_group'},
	   {name: 'study_investigator', type: 'string', mapping: 'study_investigator'},
	   {name: 'study_site', type: 'string', mapping: 'study_site'},
	   {name: 'study_country', type: 'string', mapping: 'study_country'},
	   {name: 'patient_id', type: 'int', mapping: 'patient_id'},
	   {name: 'age', type: 'string', mapping: 'age'},
	   {name: 'doi', type: 'string', mapping: 'doi'},
	   {name: 'collection_date', type: 'string', mapping: 'collection_date'},
	   {name: 'locus_name', type: 'string', mapping: 'locus_name'},
	   {name: 'locus_pos', type: 'string', mapping: 'locus_pos'},
	   {name: 'marker_type', type: 'string', mapping: 'marker_type'},
	   {name: 'geno_value', type: 'string', mapping: 'geno_value'},
	   {name: 'geno_status', type: 'string', mapping: 'geno_status'}
	   ]),           
	   listeners: {
           load: function() {
               var gridEl = wwarnDBGrid.getGridEl();
               var bbarEl = wwarnDBGrid.getBottomToolbar().getEl();
               if (wwarnDBStore.getTotalCount() == 0 && typeof gridEl == 'object') {
                   gridEl.mask('No results found.', 'x-mask');
                   bbarEl.mask();
               }
           },
       }
	});

    var wwarnCM = new Ext.grid.ColumnModel({
        columns: [
                  {
                      id: 'study_label',
                      header: 'Study Label',
                      width: 208,
                      sortable: true,
                      dataIndex: 'study_label'
                  },
                  {
                      id: 'study_investigator',
                      header: 'Investigator',
                      width: 80,
                      sortable: true,
                      dataIndex: 'study_investigator'
                  },
                  {
                      id: 'study_group',
                      header: 'Study Group',
                      width: 72,
                      sortable: true,
                      dataIndex: 'study_label',
                      hidden: true
                  },
                  {
                      id: 'study_site',
                      header: 'Site',
                      width: 60,
                      sortable: true,
                      dataIndex: 'study_site',
                      hidden: true
                  },
                  {
                      id: 'study_country',
                      header: "Country",
                      width: 70,
                      sortable: true,
                      dataIndex: 'study_country'
                  },
                  {
                      id: 'patient_id',
                      header: "Patient ID",
                      width: 68,
                      sortable: true,
                      dataIndex: 'patient_id',
                      hidden: true
                  },
                  {
                      id: 'age',
                      header: "Age",
                      width: 45,
                      sortable: true,
                      dataIndex: 'age'
                  },
                  {
                      id: 'date_of_inclusion',
                      header: "Date of Inclusion",
                      sortable: true,
                      dataIndex: 'doi',
                      hidden: true
                  },
                  {
                      id: 'collection_date',
                      header: 'Sample Collection Date',
                      width: 138,
                      sortable: true,
                      dataIndex: 'collection_date'
                  },
                  {
                      id: 'locus_name',
                      header: 'Locus Name',
                      width: 80,
                      sortable: true,
                      dataIndex: 'locus_name'
                  },
                  {
                      id: 'locus_position',
                      header: 'Locus Position',
                      sortable: true,
                      dataIndex: 'locus_pos'
                  },
                  {
                      id: 'marker_type',
                      header: 'Marker Type',
                      width: 85,
                      dataIndex: 'marker_type'
                  },
                  {
                      id: 'geno_value',
                      header: 'Value',
                      width: 70,
                      sortable: true,
                      dataIndex: 'geno_value'
                  },
                  {
                      id: 'geno_status',
                      header: 'Mutant Status',
                      width: 85,
                      sortable: true,
                      dataIndex: 'geno_status'
                  }
        ]
    });

	// Our grid is created prior to our store being
	// loaded due to my wacky design!
	wwarnDBGrid = new Ext.grid.GridPanel({
		id: 'wwarnDBGrid',
		store: wwarnDBStore,
		trackMouseOver: false,
		disableSelection: true,
		loadMask: true,
		cm: wwarnCM,
		stripeRows: true,
		height: 450,
        width: 730,
		frame: true,
        
        // Paging bar
		bbar: new Ext.PagingToolbar({
			pageSize: 25,
            store: wwarnDBStore,
			displayInfo: true,
			displayMsg: 'Displaying results {0} - {1} of {2}',
			emptyMsg: "No results to display",
            items: [
                '-', {
                    cls: 'x-btn-icon',
                    icon: 'javascript/ext/examples/shared/icons/save.gif',
                    handler: function() {
                        // We need to make sure that our store contains records prior to 
                        // attempting to save
                        if (wwarnDBStore.getTotalCount() > 0) {
                            var params = Ext.getCmp('wwarnDBGrid').getStore().baseParams;
                            Ext.apply(params, { download: "true" } );
                            
                            var report = new Ext.ux.Report({
                                renderTo: Ext.getBody()
                            });

                            report.load({
                                url: '/cgi-bin/wwarn/wwarn_db_query.cgi',
                                params: params
                            });
                        }
                    }
                }
            ]
		})
	});

    wwarnDBGrid.render('gridresults');
    wwarnDBGrid.show();
    wwarnDBGrid.el.mask("Please submit a query", 'x-mask');

});

