Ext.onReady(function() {
    Ext.QuickTips.init();

    var uploadForm = new Ext.FormPanel({
        renderTo: 'upload-form',
        fileUpload: true,
        frame: true,
        bodyStyle: 'padding: 10px 10px 0 10px;',
        width: 500,
        labelWidth: 25,
        defaults: {
            anchor: '95%',
            allowBlank: false,
            msgTarget: 'side'
        },
        items: [{
            xtype: 'fileuploadfield',
            id: 'input_data_file',
            emptyText: 'Select a data file',
            fieldLabel: 'File',
            name: 'input_data_file',
            buttonCfg: {
                text: '',
                iconCls: 'upload-icon'
            }
        }],
        buttons: [{
            text: 'Submit',
            handler: function() {
                if (uploadForm.getForm().isValid()) {
                    uploadForm.getForm().submit({
                        url: '/cgi-bin/wwarn/wwarn_convert_to_mysql.cgi',
                        waitMsg: 'Uploading your file...',
                        success: function(fp, o) {
                            var retJSON = Ext.util.JSON.decode(o.response.responseText);
                            var grid = Ext.getCmp('wwarnLogGrid');
                            grid.getStore().loadData(retJSON);
                        },
                        failure: function(fp, o) {
                            Ext.Msg.alert('ERROR', o.msg);
                        }
                    });
                }
            }
        },{
            text: 'Reset',
            handler: function() {
                uploadForm.getForm().reset();
            }
        }]
    });

    var wwarnLogStore = new Ext.data.Store({
		id: 'wwarnLogStore',
	    reader: new Ext.data.JsonReader({
		    root: 'results',
	    },[
            {name: 'wwarn_logmsg', type: 'string', mapping: 'wwarn_logmsg'},
	    ]),           
	    listeners: {
            load: function() {
                grid = Ext.getCmp('wwarnLogGrid');
                if (wwarnLogStore.getTotalCount() == 0) {
                    grid.getView().setEmptyText('No log messages to display');
                }
            },
        }
	});

    var wwarnCM = new Ext.grid.ColumnModel({
        columns: [{
            id: 'wwarn_logmsg',
            header: 'Log message',
            sortable: true,
            hideable: false,
            fixed: true,
            width: 715,
            dataIndex: 'wwarn_logmsg'
        }]
    });

	wwarnLogGrid = new Ext.grid.GridPanel({
		id: 'wwarnLogGrid',
		store: wwarnLogStore,
        viewConfig: {
            emptyText: 'Please submit a data file',
            deferEmptyText: false
        },
		trackMouseOver: false,
		disableSelection: true,
		loadMask: true,
		cm: wwarnCM,
		stripeRows: true,
		height: 450,
        width: 730,
		frame: true,
	});

    wwarnLogGrid.render('log-message');
    wwarnLogGrid.show();
});
