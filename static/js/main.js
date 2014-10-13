	var Data;
	var Graph;
	var Chart = null;
	var DistinctKeys;
	var ResourceDetailsCache = {};
	var LastEventX;
	var LastEventY;

	function hideTooltip() {
		$('#tooltip').hide();
		document.removeEventListener( 'click', hideTooltip );
	}

	function updateResourceDetails( resourceDetails ) {
		if( typeof( resourceDetails ) == 'object' ) {
			if( 'error' in resourceDetails ) {
				Text = resourceDetails['error'];
			} else {
				Text = resourceDetails['Description'];
			}
		} else {
			Text = resourceDetails;
		}

		$('#tooltip').css( 'top', LastEventY + $('#myChart').offset().top );
		$('#tooltip').css( 'left', LastEventX + $('#myChart').offset().left );

		$('#tooltiptext').html( Text.replace( /\n/g, '<br>' ) );
		$('#tooltiptext .resource_details').replaceWith( function() {
			var url = 'https://stat.ripe.net/' + $(this).text().trim();
			return '<a href="' + url + '" target="_blank">' + $(this).text() + '</a>';
		} );
		$('#tooltip').show();

		document.removeEventListener( 'click', hideTooltip );
		setTimeout( function() { document.addEventListener( 'click', hideTooltip ); }, 100 );
	}

	function getResourceDetails( resource_type, resource ) {
		if( resource_type + '-' + resource in ResourceDetailsCache ) {
			resourceDetails = ResourceDetailsCache[ resource_type + '-' + resource ];

			updateResourceDetails( resourceDetails );
		} else {
			updateResourceDetails( 'Loading details...' );

			// little timeout to allow the browser to update the previous message
			setTimeout( function() {
				$.ajax( {
					url: $SCRIPT_ROOT + '/getDetails',
					type: 'GET',
					contentType: 'application/json',
					data: {
						'resource_type': resource_type,
						'resource': resource
					},
					dataType: 'json'
				} ).done( function( resourceDetails ) {
					if( !('error' in resourceDetails) ) {
						ResourceDetailsCache[ resource_type + '-' + resource ] = resourceDetails;
					}
					updateResourceDetails( resourceDetails );
				} ).error( function( jqXHR, textStatus, errorThrown ) {
					UIAjaxError( 'Error saving the grap', jqXHR, textStatus, errorThrown );
				} );
			}, 100 );
		}
	}

	function chartClick(ev) {
		if( 'targetID' in ev ) {
			LastEventX = ev['x'];
			LastEventY = ev['y'];

			resource_type = null;

			// obtain resource type from the NfDump field used in the query

			aggrField = Graph['Query']['AggrField'];

			for( FieldIdx in GlobalConfig['NFDUMP_FIELDS'] ) {
				if( GlobalConfig['NFDUMP_FIELDS'][FieldIdx]['ID'] == aggrField ) {
					if( 'Details' in GlobalConfig['NFDUMP_FIELDS'][FieldIdx] ) {
						resource_type = GlobalConfig['NFDUMP_FIELDS'][FieldIdx]['Details'];
						break;
					}
				}
			}

			if( !resource_type ) {
				return;
			}

			// check if user clicked on something related to the query's key (area, line, legend entry)
			// if so, obtain the clicked element's index ( = key)

			targetID = ev['targetID'];

			var BreakException= {};

			elementIndex = undefined;

			[ 'area#(\\d+)', 'line#(\\d+)', 'legendentry#(\\d+)', 'bar#(\\d+)#' ].forEach( function( clickedElement ) {
				try {
					RE = new RegExp( clickedElement );
					matches = RE.exec( targetID );
					if( matches ) {
						elementIndex = parseInt( matches[1] );
						throw BreakException;
					}
				} catch(exception) {
					if (exception!==BreakException) throw exception;
				}
			} );

			if( !isNaN(elementIndex) ) {
				// obtain key's value from the clicked element
				resource = DistinctKeys[elementIndex];

				getResourceDetails( resource_type, resource );
			}
		}
	}

	function drawChart( data ) {
		Data = data['Data'];
		Graph = data['Graph'];

//		ColIdx = 'Draw' in Graph ? Graph['Draw']['What'] : Graph['ColName'];
		DrawWhat = 'Draw' in Graph ? Graph['Draw']['What'] : Graph['ColName'];
		if( DrawWhat[ DrawWhat.length-1 ] == '%' ) {
			ColIdx = DrawWhat.substr( 0, DrawWhat.length-1 );
			DrawPercentage = true;
		} else {
			ColIdx = DrawWhat;
			DrawPercentage = false;
		}

		var rows = [];
		var row = [];

		// initialize first row (column labels)

		row.push( 'Key' );

		DistinctKeys = Data['DistinctKeys'].slice(0);

		// remove Summary from distinct keys

		if( DistinctKeys.indexOf('summary') >= 0 ) {
			DistinctKeys.splice( DistinctKeys.indexOf('summary'), 1 );
		}

		DistinctKeys.forEach( function(e) {
			row.push( e );
			row.push( { type: 'string', role: 'tooltip', p: { 'html': true } } );
		} );

		rows.push( row );

		var Summary;
		var Tooltip;

		// for each epoch add all the keys

		for( EpochIdx in Data['Epoches'] ) {
			Epoch = Data['Epoches'][EpochIdx];

			// copy of Recordset; Summary will be removed so that only values will remain

			Recordset = Epoch['Recordset'].slice(0);

			// get and remove Summary record

			Summary = null

			for( RecordIdx in Recordset ) {
				Record = Recordset[RecordIdx];
				if( Record['key'] == 'summary' ) {
					Summary = Recordset.splice( RecordIdx, 1 )[0];
					break;
				}
			}

			// initialize new data row

			row = [ new Date( Data['Epoches'][EpochIdx]['Epoch']*1000 ) ];

			// for each key get its record (if present)

			for( KeyIdx in DistinctKeys ) {
				Key = DistinctKeys[KeyIdx];
				Record = null;

				for( RecordIdx in Recordset ) {
					if( Recordset[RecordIdx]['key'] == Key ) {
						// get record and remove it from epoch's recordset

						Record = Recordset.splice( RecordIdx, 1 )[0];
						break;
					}
				}

				if( Record ) {
					if( DrawPercentage ) {
						if( !(Summary) || !( ColIdx in Summary ) ) {
							UIError( 'Error while drawing the graph: the selected column "' + ColIdx + '" is not present in the summary and can\'t be drawn in a percentage form.\n' +
								'Consider changing the option in the editor panel.' );
							return;
						}
					}
					if( !( ColIdx in Record ) ) {
						ValidColumns = '';
						Object.keys( Record ).forEach( function(e) {
							if( e != 'key' ) {
								if( ValidColumns != '' ) {
									ValidColumns += ', ';
								}
								ValidColumns += e;
							}
						} );
						UIError( 'Error while drawing the graph: the selected column "' + ColIdx + '" does not exist in the query\'s output.\n' +
							'Consider changing the option in the editor panel.\n' +
							'Valid columns: ' + ValidColumns );
						return;
					}

					Tooltip = '<div class="charttooltip">';
					Tooltip += '<b>' + moment( row[0] ).format('llll') + '</b><br>';
					Tooltip += '<br>';
					Tooltip += '<b>' + Record['key'] + '</b>: ' + Record[ColIdx].toLocaleString() + ' ' + ColIdx;

					// % of total
					if( Summary ) {
						if( ColIdx in Summary ) {
							Tooltip += ' (' + ( Math.round( Record[ColIdx] / Summary[ColIdx] * 100 * 100 ) / 100 ).toFixed(2) + '%)';
						}
					}
					Tooltip += '<br>';

					// other data
					Tooltip += '<br>';
					Tooltip += '<table align="center" class="smaller">';
					[ 'bytes', 'packets', 'flows', 'bps', 'pps', 'bpp' ].forEach( function(e) {
						if( ( e != ColIdx ) && ( e != 'key' ) && ( e in Record ) ) {
							Tooltip += '<tr>';
							Tooltip += '<td align=right>' + Record[e].toLocaleString() + '</td>';
							Tooltip += '<td>' + e + '</td>';
							if( ( [ 'bytes', 'packets', 'flows' ].indexOf(e) >= 0 ) && ( e in Summary ) ) {
								Tooltip += '<td align=right>' + ( Math.round( Record[e] / Summary[e] * 100 * 100 ) / 100 ).toFixed(2) + '%';
							} else {
								Tooltip += '<td></td>';
							}
							Tooltip += '</tr>';
						}
					} );
					Tooltip += '</table>';

					Tooltip += '</div>';

					if( DrawPercentage ) {
						row.push( parseFloat( ( Math.round( Record[ColIdx] / Summary[ColIdx] * 100 * 100 ) / 100 ).toFixed(2) ) );
					} else {
						row.push( Record[ColIdx] );	// value
					}
					row.push( Tooltip );		// tooltip
				} else {
					row.push( null );	// value
					row.push( null );	// tooltip
				}
			}
			rows.push( row );
		}

		ChartData = google.visualization.arrayToDataTable( rows );

		chartOptions = {
			isStacked: true,
			title: Graph['Title'],
			vAxis: { title: DrawPercentage ? ColIdx + ' %' : ColIdx },
			tooltip: {
				isHtml: true,
				trigger: 'focus'
			},
			backgroundColor: '#FAFAFA',
			height: $(document).height() - ( $('#header').outerHeight() + $('#footer').outerHeight() )
		};

		chartDiv = 'myChart';
		chartType = 'Draw' in Graph ? Graph['Draw']['How'] : 'bar';

		switch( chartType ) {
			case 'bar':
				Chart = new google.visualization.ColumnChart( document.getElementById(chartDiv) );
				break;
			case 'area':
				Chart = new google.visualization.AreaChart( document.getElementById(chartDiv) );
				break;
			case 'lines':
				Chart = new google.visualization.LineChart( document.getElementById(chartDiv) );
				break;
			default:
				UIError( 'Unsupported chart type: ' + chartType );
		}

		google.visualization.events.addListener( Chart, 'ready', function() {
			$('#saveaspng').css( 'left', $(document).width() - $('#saveaspng').width() - 50 );
			$('#saveaspng').css( 'top', $('#header').outerHeight() + 10 );
			$('#saveaspng a').click( function(e) {
				$('#pngtosave img').attr( 'src', Chart.getImageURI() );
				$('#pngtosave img').width( 150 );
				$('#pngtosave').css( 'top', ( jQuery(window).height() - $('#pngtosave').height() ) / 2+jQuery(window).scrollTop() + "px"  );
				$('#pngtosave').css( 'left', ( jQuery(window).width() - $('#pngtosave').width() ) / 2+jQuery(window).scrollLeft() + "px"  );
				$('#pngtosave').show();
			} );
			$('#saveaspng').show();
		} );

		google.visualization.events.addListener( Chart, 'click', function (e) {
			chartClick(e);
		} );

		Chart.draw( ChartData, chartOptions );
	}


